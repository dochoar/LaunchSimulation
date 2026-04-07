"""
POST /api/simulate
Inicia una simulación en background y devuelve el simulation_id inmediatamente.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import SimulationRequest, SimulationResponse, SimulationStatus
from app.services.simulation_service import create_simulation, run_simulation_background

router = APIRouter(prefix="/api", tags=["simulate"])


@router.post("/simulate", response_model=SimulationResponse, status_code=202)
async def start_simulation(
    body: SimulationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Kick off a market simulation.

    - Creates a DB record immediately (status=pending).
    - Fires the LangGraph pipeline in the background.
    - Returns the simulation_id so the client can poll GET /api/results/{id}.
    """
    sim_id = await create_simulation(body.product, db)

    # Fire-and-forget: run the graph without blocking the response
    asyncio.create_task(run_simulation_background(sim_id, body.product))

    return SimulationResponse(
        simulation_id=sim_id,
        status=SimulationStatus.pending,
        message="Simulation started. Poll GET /api/results/{simulation_id} for progress.",
    )
