"""
Lanzador — Simulación de enjambre con señal social acumulada.

Comportamiento de enjambre:
  - Los agentes se procesan en orden cronológico (simulado).
  - Cada agente que compra, comparte o reseña contribuye a una `social_signal`.
  - Los agentes que vienen después ven esa señal y ajustan su probabilidad de compra.
  - La señal decae con el tiempo para evitar efectos artificialmente explosivos.
  - Escépticos y conservadores resisten la señal; agentes con sesgo "social proof" la amplifican.
  - Influencers contribuyen 3x al señal y son los que más la propagan.
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

# ---------------------------------------------------------------------------
# Funnel base (sin señal social)
# ---------------------------------------------------------------------------

BASE_FUNNEL = {
    InteractionType.ignored:   0.30,
    InteractionType.viewed:    0.25,
    InteractionType.clicked:   0.20,
    InteractionType.read:      0.12,
    InteractionType.purchased: 0.07,
    InteractionType.abandoned: 0.04,
    InteractionType.shared:    0.02,
}

ARCHETYPE_PURCHASE_MODIFIER = {
    Archetype.early_adopter:   2.5,
    Archetype.influencer:      1.8,
    Archetype.power_user:      1.6,
    Archetype.pragmatist:      1.0,
    Archetype.casual_user:     0.7,
    Archetype.price_sensitive: 0.5,
    Archetype.conservative:    0.4,
    Archetype.skeptic:         0.2,
}

# ---------------------------------------------------------------------------
# Parámetros del enjambre
# ---------------------------------------------------------------------------

# Cuánto señal social aporta cada tipo de acción
SWARM_CONTRIBUTION = {
    InteractionType.shared:    0.20,
    InteractionType.purchased: 0.10,
    InteractionType.reviewed:  0.08,
    InteractionType.clicked:   0.02,
}

# Multiplicador de contribución por arquetipo (influencer propaga mucho más)
ARCHETYPE_SIGNAL_MULTIPLIER = {
    Archetype.influencer:      3.0,
    Archetype.early_adopter:   1.5,
    Archetype.power_user:      1.3,
    Archetype.pragmatist:      1.0,
    Archetype.casual_user:     0.7,
    Archetype.price_sensitive: 0.6,
    Archetype.conservative:    0.5,
    Archetype.skeptic:         0.3,
}

SIGNAL_DECAY   = 0.97   # la señal decae un 3% por agente procesado
SIGNAL_CAP     = 5.0    # evita dinamicas explosivas


# ---------------------------------------------------------------------------
# Fallback de razonamiento
# ---------------------------------------------------------------------------

REASONING_TEMPLATES: dict[tuple, str] = {
    (Archetype.early_adopter, InteractionType.purchased):  "As an early adopter, I jumped at the chance to try a new tool — the price was within my range and my pain points aligned perfectly.",
    (Archetype.skeptic,       InteractionType.ignored):    "Nothing in the copy convinced me this was different from what I've tried before. I scrolled past.",
    (Archetype.price_sensitive, InteractionType.abandoned):"I was interested until I saw the price. I added it to my list but couldn't justify it right now.",
    (Archetype.pragmatist,    InteractionType.read):       "I read through everything carefully. Needs more case studies before I commit.",
    (Archetype.conservative,  InteractionType.viewed):     "I noticed it, but I prefer to wait until it has more reviews and a proven track record.",
    (Archetype.influencer,    InteractionType.shared):     "This looked exactly like something my audience needs. I shared it immediately.",
    (Archetype.power_user,    InteractionType.purchased):  "The feature set is exactly what I've been missing. Bought without hesitation.",
    (Archetype.casual_user,   InteractionType.clicked):    "The headline caught my eye. I clicked to learn more but wasn't ready to commit.",
}


def _default_reasoning(
    persona: SimulatedAgentProfile,
    interaction: InteractionType,
    product_name: str,
    social_signal: float,
) -> str:
    key = (persona.archetype, interaction)
    base = REASONING_TEMPLATES.get(key)
    if base:
        if social_signal > 1.0 and interaction == InteractionType.purchased:
            base += " Also, I'd been seeing a lot of buzz about it from people I follow."
        return base
    pain = persona.pain_points[0].topic if persona.pain_points else "general inefficiency"
    signal_note = (
        f" (influenced by growing social buzz, signal={social_signal:.1f})"
        if social_signal > 0.8 else ""
    )
    return (
        f"{persona.name} ({persona.archetype.value}, {persona.occupation}) "
        f"{interaction.value} '{product_name}' — their main concern was '{pain}' "
        f"and their WTP was ${persona.willingness_to_pay_usd:.0f}.{signal_note}"
    )


# ---------------------------------------------------------------------------
# Lógica de enjambre
# ---------------------------------------------------------------------------

def _compute_interaction(
    persona: SimulatedAgentProfile,
    price: float,
    social_signal: float,
) -> InteractionType:
    """
    Determina la acción del agente.
    La social_signal acumulada de agentes anteriores boost purchase/view/click
    y reduce ignored, con susceptibilidad diferenciada por arquetipo y sesgos.
    """
    wtp_ratio = persona.willingness_to_pay_usd / max(price, 0.01)
    purchase_mod = ARCHETYPE_PURCHASE_MODIFIER.get(persona.archetype, 1.0)

    probs = dict(BASE_FUNNEL)

    # Ajuste base por WTP y arquetipo
    purchase_boost = min(wtp_ratio * purchase_mod, 4.0)
    probs[InteractionType.purchased] *= purchase_boost

    if persona.willingness_to_pay_usd < price:
        probs[InteractionType.purchased] = 0.0
        probs[InteractionType.abandoned] *= 1.5

    if "social proof" in persona.cognitive_biases:
        probs[InteractionType.shared] *= 1.8

    # --- Efecto de enjambre ---
    if social_signal > 0:
        # Susceptibilidad: qué tanto le importa al agente lo que hacen los demás
        susceptibility = 1.0

        if "social proof" in persona.cognitive_biases:
            susceptibility *= 2.0          # muy influenciable por el grupo
        if "loss aversion" in persona.cognitive_biases:
            susceptibility *= 1.4          # miedo a perderse algo (FOMO)

        # Por arquetipo
        archetype_susceptibility = {
            Archetype.influencer:      1.6,  # siente la tendencia antes que nadie
            Archetype.early_adopter:   1.4,
            Archetype.casual_user:     1.2,
            Archetype.pragmatist:      1.0,
            Archetype.price_sensitive: 0.9,
            Archetype.power_user:      0.8,
            Archetype.conservative:    0.5,  # resistente: espera a que haya más prueba
            Archetype.skeptic:         0.2,  # casi inmune a la presión social
        }
        susceptibility *= archetype_susceptibility.get(persona.archetype, 1.0)

        boost = min(social_signal * susceptibility, 3.0)

        probs[InteractionType.purchased] *= (1 + boost * 0.45)
        probs[InteractionType.viewed]    *= (1 + boost * 0.20)
        probs[InteractionType.clicked]   *= (1 + boost * 0.30)
        probs[InteractionType.read]      *= (1 + boost * 0.15)
        probs[InteractionType.ignored]   *= max(0.05, 1 - boost * 0.35)

        # Conservadores: la señal les hace ver, pero no comprar rápido
        if persona.archetype == Archetype.conservative and social_signal > 1.5:
            probs[InteractionType.viewed] *= 1.5
            probs[InteractionType.purchased] *= 0.5  # aún necesitan tiempo

    total = sum(probs.values())
    choices = list(probs.keys())
    weights = [probs[k] / total for k in choices]
    return random.choices(choices, weights=weights, k=1)[0]


def _update_signal(
    signal: float,
    persona: SimulatedAgentProfile,
    action: InteractionType,
) -> float:
    """Acumula señal social y aplica decaimiento."""
    contribution = SWARM_CONTRIBUTION.get(action, 0.0)
    if contribution == 0.0:
        return signal * SIGNAL_DECAY

    archetype_mult = ARCHETYPE_SIGNAL_MULTIPLIER.get(persona.archetype, 1.0)
    # network_influence (1-10): cuántos peers influencia normalmente
    net_scale = persona.network_influence / 5.0
    new_signal = (signal * SIGNAL_DECAY) + (contribution * archetype_mult * net_scale)
    return min(new_signal, SIGNAL_CAP)


def _signal_label(signal: float) -> str:
    if signal < 0.2:
        return "no social buzz yet"
    if signal < 0.8:
        return f"some early buzz (signal={signal:.1f})"
    if signal < 2.0:
        return f"growing momentum (signal={signal:.1f})"
    if signal < 3.5:
        return f"strong viral wave (signal={signal:.1f})"
    return f"explosive trending (signal={signal:.1f})"


# ---------------------------------------------------------------------------
# Razonamiento en lotes (con contexto de señal social)
# ---------------------------------------------------------------------------

BATCH_SYSTEM = """\
You generate short reasoning explanations for why consumers reacted to a product.
Some agents are influenced by social buzz from earlier buyers/sharers — reflect that when relevant.
Output ONLY a valid JSON array of strings, one per agent, in the same order given.
No markdown, no preamble. Start with [ and end with ].
Example: ["Reason for agent 1.", "Reason for agent 2."]
"""


def _batch_reasoning(
    batch: list[tuple[SimulatedAgentProfile, InteractionType, float]],
    product_name: str,
    product_desc: str,
    llm,
) -> list[str]:
    lines = []
    for persona, action, signal in batch:
        social_ctx = f", context={_signal_label(signal)}" if signal > 0.2 else ""
        lines.append(
            f"- {persona.name} ({persona.archetype.value}, {persona.occupation}, "
            f"WTP ${persona.willingness_to_pay_usd:.0f}{social_ctx}): action={action.value}, "
            f"pain={persona.pain_points[0].topic if persona.pain_points else 'none'}"
        )

    prompt = (
        f"Product: '{product_name}'\nDescription excerpt: {product_desc[:300]}\n\n"
        f"Agents (explain each in 1 sentence why they took that action, "
        f"mentioning social influence when context shows buzz):\n"
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

    return [_default_reasoning(p, a, product_name, s) for p, a, s in batch]


# ---------------------------------------------------------------------------
# Nodo principal
# ---------------------------------------------------------------------------

def launcher_node(state: SimulationState) -> SimulationState:
    """
    LangGraph node: simulación de enjambre.

    Los agentes se procesan en orden. Cada acción que genera señal social
    (compra, share, reseña) incrementa social_signal, que a su vez boost
    las probabilidades de los agentes siguientes de manera diferenciada.
    """
    personas = state.get("personas", [])
    if not personas:
        return {**state, "interactions": [], "error": "No personas to simulate"}

    product = state["product"]
    llm = get_llm(temperature=0.7)

    logger.info("[Lanzador] Starting swarm simulation for %d agents...", len(personas))

    # --- Fase 1: determinar acciones en orden (enjambre) ---
    social_signal = 0.0
    agent_actions: list[tuple[SimulatedAgentProfile, InteractionType, float]] = []

    for persona in personas:
        signal_at_decision = social_signal
        action = _compute_interaction(persona, product.price_usd, social_signal)
        agent_actions.append((persona, action, signal_at_decision))
        social_signal = _update_signal(social_signal, persona, action)

    purchases = sum(1 for _, a, _ in agent_actions if a == InteractionType.purchased)
    shares    = sum(1 for _, a, _ in agent_actions if a == InteractionType.shared)
    logger.info(
        "[Lanzador] Actions done. Purchases=%d, Shares=%d, Peak signal≈%.2f",
        purchases, shares, max((s for _, _, s in agent_actions), default=0),
    )

    # --- Fase 2: razonamiento en lotes (incluye señal social como contexto) ---
    all_reasoning: list[str] = []
    for i in range(0, len(agent_actions), REASONING_BATCH_SIZE):
        batch = agent_actions[i : i + REASONING_BATCH_SIZE]
        reasons = _batch_reasoning(batch, product.name, product.description, llm)
        all_reasoning.extend(reasons)
        logger.info("[Lanzador] Reasoning batch %d-%d done.", i + 1, i + len(batch))

    # --- Fase 3: armar eventos ---
    interactions: list[AgentInteractionEvent] = []
    for (persona, action, signal), reasoning in zip(agent_actions, all_reasoning):
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

    logger.info("[Lanzador] Swarm simulation complete. %d/%d purchased.", purchases, len(personas))
    return {**state, "interactions": interactions, "error": None}
