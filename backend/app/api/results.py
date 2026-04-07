"""
GET /api/results/{simulation_id}
GET /api/results/{simulation_id}/status   ← lightweight polling endpoint
GET /api/results/{simulation_id}/personas
GET /api/results/{simulation_id}/posts
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import SimulationResult, SimulationStatus
from app.services.simulation_service import get_simulation_result

router = APIRouter(prefix="/api/results", tags=["results"])


async def _load_or_404(simulation_id: str, db: AsyncSession) -> SimulationResult:
    result = await get_simulation_result(simulation_id, db)
    if not result:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found.")
    return result


@router.get("/{simulation_id}", response_model=SimulationResult)
async def get_full_result(
    simulation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Full simulation result including personas, interactions, posts and metrics."""
    return await _load_or_404(simulation_id, db)


@router.get("/{simulation_id}/status")
async def get_status(
    simulation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Lightweight polling endpoint — returns status and error if any."""
    result = await _load_or_404(simulation_id, db)
    return {
        "simulation_id": simulation_id,
        "status": result.status,
        "error": result.error,
        "persona_count": len(result.personas),
        "interaction_count": len(result.interactions),
        "post_count": len(result.social_posts),
        "has_metrics": result.metrics is not None,
    }


@router.get("/{simulation_id}/personas")
async def get_personas(
    simulation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return only the generated personas (useful for browsing agents)."""
    result = await _load_or_404(simulation_id, db)
    if result.status not in {SimulationStatus.completed, SimulationStatus.running}:
        raise HTTPException(
            status_code=409,
            detail=f"Simulation is {result.status.value} — personas not yet available.",
        )
    return {"simulation_id": simulation_id, "personas": result.personas}


@router.get("/{simulation_id}/posts")
async def get_social_posts(
    simulation_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the generated social feed sorted by timestamp."""
    result = await _load_or_404(simulation_id, db)
    posts = sorted(result.social_posts, key=lambda p: p.timestamp_offset_hours)
    return {"simulation_id": simulation_id, "posts": posts}
