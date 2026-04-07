"""
Cronista — Analiza todos los logs de la simulación y genera métricas finales.

Produce:
  - Curva de adopción (puntos horarios)
  - Top objeciones (agrupadas por tema)
  - KPIs: conversion rate, sentiment promedio
  - 3-5 insights estratégicos en lenguaje natural
"""
from __future__ import annotations

import json
import logging
from collections import Counter, defaultdict

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import SimulationState
from app.core.llm import get_boost_llm
from app.models.schemas import (
    AdoptionDataPoint,
    AgentInteractionEvent,
    InteractionType,
    ObjectionSummary,
    SimulationMetrics,
    SocialPost,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a market analyst reviewing a product launch simulation.
Output ONLY valid JSON. No markdown. No explanation. Start with { and end with }.
Required format:
{
  "objections": [{"objection": "...", "frequency": <int>, "example_agents": ["agent_001"]}, ...],
  "insights": ["Insight 1.", "Insight 2.", "Insight 3."]
}
Generate up to 5 objections and 4 insights based on the data provided.
"""


def _build_adoption_curve(
    interactions: list[AgentInteractionEvent],
    total_agents: int,
    buckets: int = 24,
) -> list[AdoptionDataPoint]:
    """Aggregate events into hourly buckets over 72 hours."""
    max_hour = 72.0
    bucket_size = max_hour / buckets

    views = Counter()
    clicks = Counter()
    purchases = Counter()

    for ev in interactions:
        b = min(int(ev.timestamp_offset_hours / bucket_size), buckets - 1)
        if ev.interaction_type in {InteractionType.viewed, InteractionType.clicked,
                                    InteractionType.read, InteractionType.purchased,
                                    InteractionType.shared}:
            views[b] += 1
        if ev.interaction_type in {InteractionType.clicked, InteractionType.read,
                                    InteractionType.purchased}:
            clicks[b] += 1
        if ev.interaction_type == InteractionType.purchased:
            purchases[b] += 1

    curve: list[AdoptionDataPoint] = []
    cum_v = cum_c = cum_p = 0
    for b in range(buckets):
        cum_v += views[b]
        cum_c += clicks[b]
        cum_p += purchases[b]
        curve.append(
            AdoptionDataPoint(
                hour=round((b + 1) * bucket_size, 1),
                cumulative_views=cum_v,
                cumulative_clicks=cum_c,
                cumulative_purchases=cum_p,
                conversion_rate=round(cum_p / max(cum_v, 1), 4),
            )
        )
    return curve


def _llm_analysis(
    interactions: list[AgentInteractionEvent],
    posts: list[SocialPost],
    product_name: str,
    llm,
) -> tuple[list[ObjectionSummary], list[str]]:
    """Ask the LLM to extract objections and strategic insights."""
    import re

    # Cap inputs to keep context manageable for 7B models
    objection_signals = [
        f"[{e.agent_id}] {e.interaction_type.value}: {e.reasoning[:120]}"
        for e in interactions
        if e.interaction_type in {InteractionType.ignored, InteractionType.abandoned}
    ][:30]

    negative_posts = [
        f"[{p.agent_id}] {p.content[:120]}"
        for p in sorted(posts, key=lambda x: x.sentiment)[:12]
    ]

    user_msg = (
        f"Product: {product_name}\n"
        f"Negative signals:\n" + "\n".join(objection_signals) +
        "\nNegative posts:\n" + "\n".join(negative_posts)
    )

    try:
        resp = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_msg)])
        raw = re.sub(r"```(?:json)?", "", resp.content).strip()
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            raw = match.group()
        data = json.loads(raw)

        objections = [
            ObjectionSummary(
                objection=str(o.get("objection", "Unknown objection")),
                frequency=int(o.get("frequency", 1)),
                example_agents=[str(a) for a in o.get("example_agents", [])[:3]],
            )
            for o in data.get("objections", [])
        ]
        insights = [str(i) for i in data.get("insights", [])]
        return objections, insights

    except Exception as exc:
        logger.error("[Cronista] LLM analysis failed: %s", exc)
        # Deterministic fallback: derive objections from top ignored reasons
        top_reasons = [e.reasoning[:100] for e in interactions
                       if e.interaction_type == InteractionType.ignored][:5]
        fallback_objections = [
            ObjectionSummary(objection=r, frequency=1, example_agents=[]) for r in top_reasons
        ]
        return fallback_objections, [
            "Simulation completed but LLM analysis failed — review raw interaction logs.",
        ]


def chronicler_node(state: SimulationState) -> SimulationState:
    """LangGraph node: computes metrics and generates strategic insights."""
    interactions = state.get("interactions", [])
    posts = state.get("social_posts", [])
    personas = state.get("personas", [])
    product = state["product"]
    llm = get_boost_llm(temperature=0.5)

    total = len(personas)
    if total == 0:
        return {**state, "metrics": None, "error": "No personas in simulation"}

    logger.info("[Cronista] Analyzing %d interactions, %d posts...", len(interactions), len(posts))

    # --- KPIs ---
    type_counts: Counter = Counter(e.interaction_type for e in interactions)
    n_viewed = sum(
        type_counts[t]
        for t in [InteractionType.viewed, InteractionType.clicked,
                  InteractionType.read, InteractionType.purchased,
                  InteractionType.shared, InteractionType.abandoned]
    )
    n_clicked = sum(
        type_counts[t]
        for t in [InteractionType.clicked, InteractionType.read,
                  InteractionType.purchased]
    )
    n_purchased = type_counts[InteractionType.purchased]

    avg_sentiment = (
        sum(p.sentiment for p in posts) / len(posts) if posts else 0.0
    )

    # --- Adoption curve ---
    adoption_curve = _build_adoption_curve(interactions, total)

    # --- LLM analysis ---
    objections, insights = _llm_analysis(interactions, posts, product.name, llm)

    metrics = SimulationMetrics(
        total_agents=total,
        agents_who_viewed=n_viewed,
        agents_who_clicked=n_clicked,
        agents_who_purchased=n_purchased,
        overall_conversion_rate=round(n_purchased / max(n_viewed, 1), 4),
        average_sentiment=round(avg_sentiment, 3),
        top_objections=objections,
        adoption_curve=adoption_curve,
        key_insights=insights,
    )

    logger.info(
        "[Cronista] Done. Purchased: %d/%d | CR: %.1f%% | Sentiment: %.2f",
        n_purchased, total,
        metrics.overall_conversion_rate * 100,
        avg_sentiment,
    )

    return {**state, "metrics": metrics, "error": None}
