"""
Poblador — Crea la memoria vectorial persistente de cada persona en ChromaDB.

Construye documentos ricos a partir del perfil y los indexa para que el
Agente Entrevistador pueda recuperarlos con RAG.
"""
from __future__ import annotations

import logging

from app.agents.state import SimulationState
from app.models.schemas import SimulatedAgentProfile
from app.services.vector_store import upsert_agent_memory

logger = logging.getLogger(__name__)


def _build_agent_documents(persona: SimulatedAgentProfile, product_name: str) -> list[str]:
    """Convert a persona into indexable text chunks for ChromaDB."""
    pain_points_text = "; ".join(
        f"{pp.topic} (intensity {pp.intensity}/10)" for pp in persona.pain_points
    )
    goals_text = "; ".join(persona.goals)
    biases_text = ", ".join(persona.cognitive_biases)
    channels_text = ", ".join(c.value for c in persona.preferred_channels)

    return [
        # Chunk 1: Core identity
        (
            f"My name is {persona.name}. I am {persona.age} years old, {persona.gender}, "
            f"living in {persona.location}. I work as {persona.occupation} and earn "
            f"approximately ${persona.annual_income_usd:,.0f} USD per year. "
            f"My consumer archetype is '{persona.archetype.value}'. "
            f"My tech savviness is {persona.tech_savviness}/10."
        ),
        # Chunk 2: Pain points & goals
        (
            f"My main pain points are: {pain_points_text}. "
            f"My current goals are: {goals_text}. "
            f"I am primarily reached through: {channels_text}."
        ),
        # Chunk 3: Psychology & WTP
        (
            f"My cognitive biases include: {biases_text}. "
            f"When evaluating '{product_name}' at its listed price, my maximum willingness to pay "
            f"is ${persona.willingness_to_pay_usd:.2f} USD. "
            f"This reflects my income level and how urgently I need this type of solution."
        ),
        # Chunk 4: Bio narrative
        persona.bio,
    ]


def populator_node(state: SimulationState) -> SimulationState:
    """LangGraph node: indexes all personas into ChromaDB."""
    personas = state.get("personas", [])
    if not personas:
        logger.warning("[Poblador] No personas to populate.")
        return {**state, "populated_agent_ids": [], "error": "No personas generated"}

    simulation_id = state["simulation_id"]
    product_name = state["product"].name
    populated_ids: list[str] = []

    logger.info("[Poblador] Indexing %d agents into ChromaDB...", len(personas))

    for persona in personas:
        try:
            docs = _build_agent_documents(persona, product_name)
            metadatas = [
                {
                    "agent_id": persona.agent_id,
                    "sim_id": simulation_id,
                    "chunk_type": chunk_type,
                    "archetype": persona.archetype.value,
                    "age": persona.age,
                    "income": persona.annual_income_usd,
                }
                for chunk_type in ["identity", "pain_points", "psychology", "bio"]
            ]
            ids = [
                f"{persona.agent_id}_identity",
                f"{persona.agent_id}_pain_points",
                f"{persona.agent_id}_psychology",
                f"{persona.agent_id}_bio",
            ]
            upsert_agent_memory(
                simulation_id=simulation_id,
                agent_id=persona.agent_id,
                documents=docs,
                metadatas=metadatas,
                ids=ids,
            )
            populated_ids.append(persona.agent_id)
        except Exception as exc:
            logger.error("[Poblador] Failed to index %s: %s", persona.agent_id, exc)

    logger.info("[Poblador] Indexed %d / %d agents.", len(populated_ids), len(personas))
    return {**state, "populated_agent_ids": populated_ids, "error": None}
