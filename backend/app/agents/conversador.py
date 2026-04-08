"""
Conversador — Genera posts sociales simulados en LOTES.

Cambio vs versión anterior:
  - Antes: 1 llamada LLM por agente (N agentes = N llamadas).
  - Ahora: POST_BATCH_SIZE agentes por llamada (N agentes = N/5 llamadas).
  - Si el lote falla, fallback a posts deterministas basados en el reasoning.
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

POST_BATCH_SIZE = 5  # posts generados por llamada LLM

ACTIVE_INTERACTIONS = {
    InteractionType.purchased,
    InteractionType.abandoned,
    InteractionType.shared,
    InteractionType.reviewed,
    InteractionType.clicked,
}

PLATFORMS = ["twitter", "reddit", "product_hunt", "app_store"]

PLATFORM_CONFIG = {
    "twitter":      {"tone": "casual, brief, hashtags optional", "max_chars": 280},
    "reddit":       {"tone": "detailed, candid, paragraph format", "max_chars": 800},
    "product_hunt": {"tone": "constructive, startup-friendly", "max_chars": 400},
    "app_store":    {"tone": "direct review, star-rating mindset", "max_chars": 300},
}

BATCH_SYSTEM = """\
You generate realistic social media posts from consumers about a product they just encountered.
Output ONLY a valid JSON array, one object per consumer, in the same order given.
Each object must have exactly these keys:
{"content": "...", "sentiment": <-1.0 to 1.0>, "upvotes": <int>, "replies": ["...", "..."]}
No markdown, no preamble. Start with [ and end with ].
"""


def _select_platform(persona: SimulatedAgentProfile) -> str:
    channel_map = {
        "social_media":  ["twitter", "reddit"],
        "email":         ["product_hunt"],
        "paid_ads":      ["twitter"],
        "seo":           ["reddit"],
        "word_of_mouth": ["reddit", "product_hunt"],
        "app_store":     ["app_store"],
    }
    candidates = []
    for ch in persona.preferred_channels:
        candidates.extend(channel_map.get(ch.value, []))
    return random.choice(candidates) if candidates else random.choice(PLATFORMS)


def _fallback_post(
    persona: SimulatedAgentProfile,
    interaction: AgentInteractionEvent,
    platform: str,
) -> SocialPost:
    sentiment = 0.5 if interaction.interaction_type == InteractionType.purchased else -0.2
    return SocialPost(
        agent_id=persona.agent_id,
        platform=platform,
        content=interaction.reasoning[:280],
        sentiment=sentiment,
        timestamp_offset_hours=interaction.timestamp_offset_hours + random.uniform(0.5, 6.0),
        upvotes=random.randint(0, 50),
        replies=[],
    )


def _generate_batch(
    items: list[tuple[SimulatedAgentProfile, AgentInteractionEvent, str]],
    product_name: str,
    product_price: float,
    llm,
) -> list[SocialPost]:
    """Generate a batch of social posts in a single LLM call."""
    lines = []
    for persona, event, platform in items:
        config = PLATFORM_CONFIG[platform]
        lines.append(
            f"- {persona.name}, {persona.age}yo {persona.occupation} ({persona.archetype.value}). "
            f"Action: {event.interaction_type.value}. Why: {event.reasoning[:150]}. "
            f"Platform: {platform} ({config['tone']}, max {config['max_chars']} chars)."
        )

    prompt = (
        f"Product: '{product_name}' (${product_price:.2f})\n\n"
        f"Write one authentic social post per consumer below:\n"
        + "\n".join(lines)
        + f"\n\nReturn a JSON array of exactly {len(items)} objects."
    )

    try:
        resp = llm.invoke([SystemMessage(content=BATCH_SYSTEM), HumanMessage(content=prompt)])
        raw = re.sub(r"```(?:json)?", "", resp.content).strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if isinstance(parsed, list) and len(parsed) == len(items):
                posts = []
                for (persona, event, platform), data in zip(items, parsed):
                    posts.append(SocialPost(
                        agent_id=persona.agent_id,
                        platform=platform,
                        content=str(data.get("content", event.reasoning[:200])),
                        sentiment=float(data.get("sentiment", 0.0)),
                        timestamp_offset_hours=event.timestamp_offset_hours + random.uniform(0.5, 6.0),
                        upvotes=int(data.get("upvotes", 0)),
                        replies=[str(r) for r in data.get("replies", [])],
                    ))
                return posts
    except Exception as exc:
        logger.warning("[Conversador] Batch post generation failed: %s — using fallbacks.", exc)

    # Fallback: one deterministic post per item
    return [_fallback_post(persona, event, platform) for persona, event, platform in items]


def conversador_node(state: SimulationState) -> SimulationState:
    """LangGraph node: generates social posts in batches (POST_BATCH_SIZE per LLM call)."""
    personas = state.get("personas", [])
    interactions = state.get("interactions", [])
    product = state["product"]
    llm = get_llm(temperature=0.85)

    persona_map = {p.agent_id: p for p in personas}
    active = [e for e in interactions if e.interaction_type in ACTIVE_INTERACTIONS]

    logger.info(
        "[Conversador] Generating posts for %d active agents in batches of %d...",
        len(active), POST_BATCH_SIZE,
    )

    # Build (persona, event, platform) tuples
    items: list[tuple[SimulatedAgentProfile, AgentInteractionEvent, str]] = []
    for event in active:
        persona = persona_map.get(event.agent_id)
        if persona:
            items.append((persona, event, _select_platform(persona)))

    # Process in batches
    posts: list[SocialPost] = []
    for i in range(0, len(items), POST_BATCH_SIZE):
        batch = items[i : i + POST_BATCH_SIZE]
        batch_posts = _generate_batch(batch, product.name, product.price_usd, llm)
        posts.extend(batch_posts)
        logger.info("[Conversador] Batch %d-%d done (%d posts).", i + 1, i + len(batch), len(batch_posts))

    logger.info("[Conversador] Generated %d social posts total.", len(posts))
    return {**state, "social_posts": posts, "error": None}
