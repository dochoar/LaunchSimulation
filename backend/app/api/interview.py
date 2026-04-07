"""
POST /api/interview/{simulation_id}/{agent_id}
Habla con un agente simulado específico usando RAG sobre su memoria en ChromaDB.

GET  /api/interview/{simulation_id}/agents
Lista los agentes disponibles con su resultado (purchased / not) para facilitar
la selección desde el frontend.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.interviewer import interview_agent
from app.core.database import get_db
from app.models.orm import AgentMemoryORM
from app.models.schemas import InterviewRequest, InterviewResponse, SimulationStatus
from app.services.simulation_service import get_agent_data, get_simulation_result

router = APIRouter(prefix="/api/interview", tags=["interview"])


@router.get("/{simulation_id}/agents")
async def list_interviewable_agents(
    simulation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Return a lightweight list of all agents in this simulation,
    including whether they purchased and their sentiment score.
    Useful for the frontend agent-picker UI.
    """
    result = await db.execute(
        select(AgentMemoryORM)
        .where(AgentMemoryORM.simulation_id == simulation_id)
        .order_by(AgentMemoryORM.agent_id)
    )
    rows = result.scalars().all()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No agents found for simulation '{simulation_id}'. "
                   "Make sure the simulation has completed.",
        )

    return {
        "simulation_id": simulation_id,
        "agents": [
            {
                "agent_id": row.agent_id,
                "purchased": row.purchased,
                "sentiment_score": row.sentiment_score,
                "chroma_collection": row.chroma_collection,
            }
            for row in rows
        ],
    }


@router.post("/{simulation_id}/{agent_id}", response_model=InterviewResponse)
async def interview(
    simulation_id: str,
    agent_id: str,
    body: InterviewRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Chat with a specific simulated agent using RAG.

    The agent answers in first person, drawing on:
    - Their ChromaDB persona memory (retrieved via semantic search)
    - Their recorded interaction and reasoning
    - Their social post (if any)
    """
    # Guard: simulation must exist and be completed
    sim_result = await get_simulation_result(simulation_id, db)
    if not sim_result:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found.")
    if sim_result.status != SimulationStatus.completed:
        raise HTTPException(
            status_code=409,
            detail=f"Simulation is still {sim_result.status.value}. "
                   "Interview is only available once the simulation completes.",
        )

    # Load agent-specific data
    persona, interaction, post = await get_agent_data(simulation_id, agent_id, db)
    if not persona:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found in simulation '{simulation_id}'.",
        )

    response = interview_agent(
        simulation_id=simulation_id,
        persona=persona,
        interaction=interaction,
        social_post=post,
        question=body.question,
    )
    return response
