"""
POST /api/simulate/from-brief
Acepta un product brief en texto libre, lo parsea a ProductInput, y lanza la simulación.
"""
import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import SimulationResponse, SimulationStatus
from app.services.simulation_service import create_simulation, run_simulation_background
from app.utils.brief_parser import parse_brief

router = APIRouter(prefix="/api", tags=["brief"])


class BriefRequest(BaseModel):
    brief_text: str = Field(..., min_length=100, description="Raw product brief (markdown or plain text)")
    num_agents: int = Field(default=10, ge=1, le=2000, description="Number of personas to simulate")


@router.post("/simulate/from-brief", response_model=SimulationResponse, status_code=202)
async def simulate_from_brief(
    body: BriefRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Parse a free-text product brief and kick off a market simulation.

    The brief can be any format: markdown deck, plain text, copy-pasted PDF.
    The parser extracts: product name, description, price, channel, and target market.
    """
    try:
        product = parse_brief(body.brief_text, num_agents=body.num_agents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse brief: {exc}")

    sim_id = await create_simulation(product, db)
    asyncio.create_task(run_simulation_background(sim_id, product))

    return SimulationResponse(
        simulation_id=sim_id,
        status=SimulationStatus.pending,
        message=f"Simulation started for '{product.name}'. Poll GET /api/results/{sim_id}.",
    )
