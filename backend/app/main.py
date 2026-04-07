from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
import app.models.orm  # noqa: F401 — registers ORM models with Base.metadata
from app.api.simulate import router as simulate_router
from app.api.results import router as results_router
from app.api.interview import router as interview_router
from app.api.brief import router as brief_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="LaunchSim API",
    description="Multi-agent market simulation engine",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulate_router)
app.include_router(results_router)
app.include_router(interview_router)
app.include_router(brief_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
