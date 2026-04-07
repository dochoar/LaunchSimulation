"""
Conversador — Genera el log de interacciones sociales simuladas.

Produce tweets, reviews de producto y hilos de Reddit para los agentes
que interactuaron significativamente (viewed, clicked, purchased, abandoned).

Adaptado para modelos locales 7B:
  - Prompt más corto y directivo
  - Reparación de JSON robusta con regex fallback
  - Si el modelo no devuelve JSON válido, construye un post simple desde el reasoning
"""
from __future__ import annotations

import json
import logging
import random
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import SimulationState
from app.core.llm import get_llm
from app.models.schemas import (
    AgentInteractionEvent,
    InteractionType,
    SimulatedAgentProfile,
    SocialPost,
)

logger = logging.getLogger(__name__)

ACTIVE_INTERACTIONS = {
    InteractionType.purchased,
    InteractionType.abandoned,
    InteractionType.shared,
    InteractionType.reviewed,
    InteractionType.clicked,
}

PLATFORMS = ["twitter", "reddit", "product_hunt", "app_store"]

SYSTEM_PROMPT = """\
Write a realistic social media post from a consumer's perspective about a product.
Output ONLY a JSON object with these exact keys:
{"content": "...", "sentiment": <-1.0 to 1.0>, "upvotes": <int>, "replies": ["...", "..."]}
No markdown. No explanation. Start with { and end with }.
"""

USER_TEMPLATE = """\
Consumer: {name}, {age}yo {occupation} in {location}. Archetype: {archetype}.
Product: '{product_name}' (${price:.2f}). Their action: {action}.
Why: {reasoning}
Platform: {platform} ({tone}, max {max_chars} chars).
Write the post as this person. Use natural, authentic language for this platform.
"""

PLATFORM_CONFIG = {
    "twitter": {"tone": "casual, brief, hashtags optional", "max_chars": 280},
    "reddit": {"tone": "detailed, candid, paragraph format", "max_chars": 800},
    "product_hunt": {"tone": "constructive, startup-friendly", "max_chars": 400},
    "app_store": {"tone": "direct review, star-rating mindset", "max_chars": 300},
}


def _select_platform(persona: SimulatedAgentProfile) -> str:
    """Pick platform weighted by persona's preferred channels."""
    channel_map = {
        "social_media": ["twitter", "reddit"],
        "email": ["product_hunt"],
        "paid_ads": ["twitter"],
        "seo": ["reddit"],
        "word_of_mouth": ["reddit", "product_hunt"],
        "app_store": ["app_store"],
    }
    candidates = []
    for ch in persona.preferred_channels:
        candidates.extend(channel_map.get(ch.value, []))
    if not candidates:
        candidates = PLATFORMS
    return random.choice(candidates)


def _generate_post(
    persona: SimulatedAgentProfile,
    interaction: AgentInteractionEvent,
    product_price: float,
    llm,
) -> SocialPost | None:
    platform = _select_platform(persona)
    config = PLATFORM_CONFIG[platform]

    user_msg = USER_TEMPLATE.format(
        name=persona.name,
        age=persona.age,
        occupation=persona.occupation,
        location=persona.location,
        archetype=persona.archetype.value,
        biases=", ".join(persona.cognitive_biases),
        pain_points="; ".join(pp.topic for pp in persona.pain_points),
        product_name=interaction.product_name,
        price=product_price,
        action=interaction.interaction_type.value,
        reasoning=interaction.reasoning,
        platform=platform,
        tone=config["tone"],
        max_chars=config["max_chars"],
    )

    try:
        resp = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)])
        raw = resp.content.strip()

        # JSON repair: strip fences, find first {...} block
        raw = re.sub(r"```(?:json)?", "", raw).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group()
        data = json.loads(raw)

        return SocialPost(
            agent_id=persona.agent_id,
            platform=platform,
            content=str(data.get("content", interaction.reasoning[:200])),
            sentiment=float(data.get("sentiment", 0.0)),
            timestamp_offset_hours=interaction.timestamp_offset_hours + random.uniform(0.5, 6.0),
            upvotes=int(data.get("upvotes", 0)),
            replies=[str(r) for r in data.get("replies", [])],
        )
    except Exception as exc:
        logger.warning("[Conversador] Post gen failed for %s: %s — using fallback.", persona.agent_id, exc)
        # Deterministic fallback: build a minimal post from the reasoning
        sentiment = 0.5 if interaction.interaction_type.value == "purchased" else -0.2
        return SocialPost(
            agent_id=persona.agent_id,
            platform=platform,
            content=interaction.reasoning[:280],
            sentiment=sentiment,
            timestamp_offset_hours=interaction.timestamp_offset_hours + random.uniform(0.5, 6.0),
            upvotes=random.randint(0, 50),
            replies=[],
        )


def conversador_node(state: SimulationState) -> SimulationState:
    """LangGraph node: generates social posts for active agents."""
    personas = state.get("personas", [])
    interactions = state.get("interactions", [])
    product = state["product"]
    llm = get_llm(temperature=0.85)

    # Index personas by agent_id
    persona_map = {p.agent_id: p for p in personas}

    # Only generate posts for agents who engaged (not ignored)
    active = [e for e in interactions if e.interaction_type in ACTIVE_INTERACTIONS]

    logger.info("[Conversador] Generating posts for %d / %d active agents...", len(active), len(interactions))

    posts: list[SocialPost] = []
    for event in active:
        persona = persona_map.get(event.agent_id)
        if not persona:
            continue
        post = _generate_post(persona, event, product.price_usd, llm)
        if post:
            posts.append(post)

    logger.info("[Conversador] Generated %d social posts.", len(posts))
    return {**state, "social_posts": posts, "error": None}
