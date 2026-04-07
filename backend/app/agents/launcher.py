"""
Lanzador — Simulación probabilística de interacciones.

Adaptado para modelos locales 7B:
  - La acción de cada agente es DETERMINISTA (probabilidades ajustadas por perfil, sin LLM)
  - El reasoning se genera en LOTES de 10 agentes por llamada LLM
  - Si un lote falla, usa templates de reasoning basados en arquetipo + acción (sin LLM)
"""
from __future__ import annotations

import json
import logging
import random
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import SimulationState
from app.core.llm import get_llm
from app.models.schemas import (
    AgentInteractionEvent,
    Archetype,
    InteractionType,
    SimulatedAgentProfile,
)

logger = logging.getLogger(__name__)

REASONING_BATCH_SIZE = 10

BASE_FUNNEL = {
    InteractionType.ignored: 0.30,
    InteractionType.viewed: 0.25,
    InteractionType.clicked: 0.20,
    InteractionType.read: 0.12,
    InteractionType.purchased: 0.07,
    InteractionType.abandoned: 0.04,
    InteractionType.shared: 0.02,
}

ARCHETYPE_PURCHASE_MODIFIER = {
    Archetype.early_adopter: 2.5,
    Archetype.influencer: 1.8,
    Archetype.power_user: 1.6,
    Archetype.pragmatist: 1.0,
    Archetype.casual_user: 0.7,
    Archetype.price_sensitive: 0.5,
    Archetype.conservative: 0.4,
    Archetype.skeptic: 0.2,
}

# Deterministic fallback templates
REASONING_TEMPLATES: dict[tuple, str] = {
    (Archetype.early_adopter, InteractionType.purchased): "As an early adopter, I jumped at the chance to try a new tool — the price was within my range and my pain points aligned perfectly.",
    (Archetype.skeptic, InteractionType.ignored): "Nothing in the copy convinced me this was different from what I've tried before. I scrolled past.",
    (Archetype.price_sensitive, InteractionType.abandoned): "I was interested until I saw the price. I added it to my list but couldn't justify it right now.",
    (Archetype.pragmatist, InteractionType.read): "I read through everything carefully. Needs more case studies before I commit.",
    (Archetype.conservative, InteractionType.viewed): "I noticed it, but I prefer to wait until it has more reviews and a proven track record.",
    (Archetype.influencer, InteractionType.shared): "This looked exactly like something my audience needs. I shared it immediately.",
    (Archetype.power_user, InteractionType.purchased): "The feature set is exactly what I've been missing. Bought without hesitation.",
    (Archetype.casual_user, InteractionType.clicked): "The headline caught my eye. I clicked to learn more but wasn't ready to commit.",
}


def _default_reasoning(persona: SimulatedAgentProfile, interaction: InteractionType, product_name: str) -> str:
    key = (persona.archetype, interaction)
    if key in REASONING_TEMPLATES:
        return REASONING_TEMPLATES[key]
    pain = persona.pain_points[0].topic if persona.pain_points else "general inefficiency"
    return (
        f"{persona.name} ({persona.archetype.value}, {persona.occupation}) "
        f"{interaction.value} '{product_name}' — their main concern was '{pain}' "
        f"and their WTP was ${persona.willingness_to_pay_usd:.0f}."
    )


def _compute_interaction(persona: SimulatedAgentProfile, price: float) -> InteractionType:
    wtp_ratio = persona.willingness_to_pay_usd / max(price, 0.01)
    purchase_mod = ARCHETYPE_PURCHASE_MODIFIER.get(persona.archetype, 1.0)

    probs = dict(BASE_FUNNEL)
    purchase_boost = min(wtp_ratio * purchase_mod, 4.0)
    probs[InteractionType.purchased] *= purchase_boost

    if persona.willingness_to_pay_usd < price:
        probs[InteractionType.purchased] = 0.0
        probs[InteractionType.abandoned] *= 1.5

    if "social proof" in persona.cognitive_biases:
        probs[InteractionType.shared] *= 1.8

    total = sum(probs.values())
    choices = list(probs.keys())
    weights = [probs[k] / total for k in choices]
    return random.choices(choices, weights=weights, k=1)[0]


BATCH_SYSTEM = """\
You generate short reasoning explanations for why consumers reacted to a product.
Output ONLY a valid JSON array of strings, one per agent, in the same order given.
No markdown, no preamble. Start with [ and end with ].
Example: ["Reason for agent 1.", "Reason for agent 2."]
"""


def _batch_reasoning(
    batch: list[tuple[SimulatedAgentProfile, InteractionType]],
    product_name: str,
    product_desc: str,
    llm,
) -> list[str]:
    lines = []
    for persona, action in batch:
        lines.append(
            f"- {persona.name} ({persona.archetype.value}, {persona.occupation}, "
            f"WTP ${persona.willingness_to_pay_usd:.0f}): action={action.value}, "
            f"pain={persona.pain_points[0].topic if persona.pain_points else 'none'}"
        )

    prompt = (
        f"Product: '{product_name}'\nDescription excerpt: {product_desc[:300]}\n\n"
        f"Agents (explain each in 1 sentence why they took that action):\n"
        + "\n".join(lines)
        + f"\n\nReturn a JSON array of exactly {len(batch)} short strings."
    )

    try:
        resp = llm.invoke([SystemMessage(content=BATCH_SYSTEM), HumanMessage(content=prompt)])
        raw = re.sub(r"```(?:json)?", "", resp.content).strip()
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            result = json.loads(match.group())
            if isinstance(result, list) and len(result) == len(batch):
                return [str(r) for r in result]
    except Exception as exc:
        logger.warning("[Lanzador] Batch reasoning failed: %s", exc)

    # Fallback: use deterministic templates
    return [_default_reasoning(p, a, product_name) for p, a in batch]


def launcher_node(state: SimulationState) -> SimulationState:
    """LangGraph node: probabilistic simulation + batched LLM reasoning."""
    personas = state.get("personas", [])
    if not personas:
        return {**state, "interactions": [], "error": "No personas to simulate"}

    product = state["product"]
    llm = get_llm(temperature=0.7)
    interactions: list[AgentInteractionEvent] = []

    logger.info("[Lanzador] Simulating %d agents...", len(personas))

    # Step 1: determine all actions (pure probability, no LLM)
    agent_actions: list[tuple[SimulatedAgentProfile, InteractionType]] = []
    for persona in personas:
        action = _compute_interaction(persona, product.price_usd)
        agent_actions.append((persona, action))

    # Step 2: generate reasoning in batches
    all_reasoning: list[str] = []
    for i in range(0, len(agent_actions), REASONING_BATCH_SIZE):
        batch = agent_actions[i : i + REASONING_BATCH_SIZE]
        reasons = _batch_reasoning(batch, product.name, product.description, llm)
        all_reasoning.extend(reasons)
        logger.info("[Lanzador] Reasoning batch %d-%d done.", i + 1, i + len(batch))

    # Step 3: assemble events
    for i, ((persona, action), reasoning) in enumerate(zip(agent_actions, all_reasoning)):
        hour_offset = random.betavariate(1.5, 4.0) * 72.0
        interactions.append(
            AgentInteractionEvent(
                agent_id=persona.agent_id,
                interaction_type=action,
                timestamp_offset_hours=round(hour_offset, 2),
                reasoning=reasoning,
                product_name=product.name,
            )
        )

    purchases = sum(1 for e in interactions if e.interaction_type == InteractionType.purchased)
    logger.info("[Lanzador] Done. %d/%d purchased.", purchases, len(personas))
    return {**state, "interactions": interactions, "error": None}
