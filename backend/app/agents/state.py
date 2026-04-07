"""
LangGraph shared state — passed between every node in the simulation graph.
"""
from __future__ import annotations

from typing import TypedDict

from app.models.schemas import (
    AgentInteractionEvent,
    ProductInput,
    SimulatedAgentProfile,
    SimulationMetrics,
    SocialPost,
)


class SimulationState(TypedDict):
    # Set at graph entry
    simulation_id: str
    product: ProductInput

    # Populated by Researcher
    market_research: str | None

    # Populated by Etnógrafo
    personas: list[SimulatedAgentProfile]

    # Populated by Poblador (collection names stored in ChromaDB)
    populated_agent_ids: list[str]

    # Populated by Lanzador
    interactions: list[AgentInteractionEvent]

    # Populated by Conversador
    social_posts: list[SocialPost]

    # Populated by Cronista
    metrics: SimulationMetrics | None

    # Error propagation
    error: str | None
