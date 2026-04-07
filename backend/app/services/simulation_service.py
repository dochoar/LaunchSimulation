"""
Simulation service — orchestrates the LangGraph run and persists results to SQLite.

Runs the graph in a background thread (via asyncio.to_thread) so the
POST /simulate endpoint returns immediately with a simulation_id.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import simulation_graph
from app.agents.state import SimulationState
from app.core.database import AsyncSessionLocal
from app.models.orm import AgentMemoryORM, SimulationORM
from app.models.schemas import (
    ProductInput,
    SimulationResult,
    SimulationStatus,
)
from app.services.vector_store import collection_name

logger = logging.getLogger(__name__)


async def create_simulation(product: ProductInput, db: AsyncSession) -> str:
    """Create a DB record and return the new simulation_id."""
    sim_id = str(uuid.uuid4())
    record = SimulationORM(
        id=sim_id,
        status=SimulationStatus.pending.value,
        product_json=product.model_dump_json(),
    )
    db.add(record)
    await db.commit()
    return sim_id


async def run_simulation_background(simulation_id: str, product: ProductInput) -> None:
    """
    Called via asyncio.create_task — runs the LangGraph graph and
    persists every stage of results back to SQLite.
    """
    logger.info("[Service] Starting simulation %s", simulation_id)

    async with AsyncSessionLocal() as db:
        # Mark as running
        record = await _get_record(db, simulation_id)
        record.status = SimulationStatus.running.value
        await db.commit()

    try:
        initial_state: SimulationState = {
            "simulation_id": simulation_id,
            "product": product,
            "personas": [],
            "populated_agent_ids": [],
            "interactions": [],
            "social_posts": [],
            "metrics": None,
            "error": None,
        }

        # Run the graph in a thread (LangGraph is sync)
        final_state: SimulationState = await asyncio.to_thread(
            simulation_graph.invoke, initial_state
        )

        async with AsyncSessionLocal() as db:
            record = await _get_record(db, simulation_id)

            if final_state.get("error") and not final_state.get("personas"):
                record.status = SimulationStatus.failed.value
                record.error = final_state["error"]
            else:
                record.status = SimulationStatus.completed.value
                record.set_personas(
                    [p.model_dump() for p in final_state.get("personas", [])]
                )
                record.set_interactions(
                    [i.model_dump() for i in final_state.get("interactions", [])]
                )
                record.set_social_posts(
                    [s.model_dump() for s in final_state.get("social_posts", [])]
                )
                if final_state.get("metrics"):
                    record.set_metrics(final_state["metrics"].model_dump())

                # Persist agent memory index
                await _persist_memory_index(db, simulation_id, final_state)

            record.updated_at = datetime.now(timezone.utc)
            await db.commit()

        logger.info("[Service] Simulation %s completed.", simulation_id)

    except Exception as exc:
        logger.exception("[Service] Simulation %s failed: %s", simulation_id, exc)
        async with AsyncSessionLocal() as db:
            record = await _get_record(db, simulation_id)
            record.status = SimulationStatus.failed.value
            record.error = str(exc)
            record.updated_at = datetime.now(timezone.utc)
            await db.commit()


async def get_simulation_result(
    simulation_id: str, db: AsyncSession
) -> SimulationResult | None:
    """Load a simulation result from SQLite."""
    record = await _get_record(db, simulation_id)
    if not record:
        return None

    from app.models.schemas import (
        AgentInteractionEvent,
        SimulatedAgentProfile,
        SocialPost,
        SimulationMetrics,
    )

    product = ProductInput(**record.get_product())

    personas = [SimulatedAgentProfile(**p) for p in record.get_personas()]
    interactions = [AgentInteractionEvent(**i) for i in record.get_interactions()]
    posts = [SocialPost(**s) for s in record.get_social_posts()]

    raw_metrics = record.get_metrics()
    metrics = SimulationMetrics(**raw_metrics) if raw_metrics else None

    return SimulationResult(
        simulation_id=simulation_id,
        status=SimulationStatus(record.status),
        product=product,
        personas=personas,
        interactions=interactions,
        social_posts=posts,
        metrics=metrics,
        error=record.error,
    )


async def get_agent_data(simulation_id: str, agent_id: str, db: AsyncSession):
    """
    Return (persona, interaction, social_post) for a specific agent.
    All three can be None if not found.
    """
    result = await get_simulation_result(simulation_id, db)
    if not result:
        return None, None, None

    persona = next((p for p in result.personas if p.agent_id == agent_id), None)
    interaction = next((i for i in result.interactions if i.agent_id == agent_id), None)
    post = next((s for s in result.social_posts if s.agent_id == agent_id), None)

    return persona, interaction, post


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_record(db: AsyncSession, simulation_id: str) -> SimulationORM | None:
    result = await db.execute(
        select(SimulationORM).where(SimulationORM.id == simulation_id)
    )
    return result.scalar_one_or_none()


async def _persist_memory_index(
    db: AsyncSession, simulation_id: str, state: SimulationState
) -> None:
    """Store AgentMemoryORM rows linking each agent to their ChromaDB collection."""
    interactions_by_agent = {
        i.agent_id: i for i in state.get("interactions", [])
    }
    posts_by_agent = {
        p.agent_id: p for p in state.get("social_posts", [])
    }

    from app.models.schemas import InteractionType

    for persona in state.get("personas", []):
        interaction = interactions_by_agent.get(persona.agent_id)
        post = posts_by_agent.get(persona.agent_id)

        purchased = (
            interaction.interaction_type == InteractionType.purchased
            if interaction else False
        )
        sentiment = post.sentiment if post else 0.0

        mem = AgentMemoryORM(
            simulation_id=simulation_id,
            agent_id=persona.agent_id,
            chroma_collection=collection_name(simulation_id, persona.agent_id),
            purchased=purchased,
            sentiment_score=sentiment,
        )
        db.add(mem)
