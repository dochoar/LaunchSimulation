"""
SQLAlchemy ORM models — persists simulation state to SQLite.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SimulationORM(Base):
    """Top-level simulation record. One row per /simulate call."""

    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    # Serialised ProductInput
    product_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Serialised lists (JSON arrays of dicts)
    personas_json: Mapped[str] = mapped_column(Text, default="[]")
    interactions_json: Mapped[str] = mapped_column(Text, default="[]")
    social_posts_json: Mapped[str] = mapped_column(Text, default="[]")
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )

    # ------------------------------------------------------------------
    # Convenience helpers to (de)serialize JSON columns
    # ------------------------------------------------------------------

    def get_personas(self) -> list[dict]:
        return json.loads(self.personas_json or "[]")

    def set_personas(self, data: list[dict]) -> None:
        self.personas_json = json.dumps(data, ensure_ascii=False)

    def get_interactions(self) -> list[dict]:
        return json.loads(self.interactions_json or "[]")

    def set_interactions(self, data: list[dict]) -> None:
        self.interactions_json = json.dumps(data, ensure_ascii=False)

    def get_social_posts(self) -> list[dict]:
        return json.loads(self.social_posts_json or "[]")

    def set_social_posts(self, data: list[dict]) -> None:
        self.social_posts_json = json.dumps(data, ensure_ascii=False)

    def get_metrics(self) -> dict | None:
        return json.loads(self.metrics_json) if self.metrics_json else None

    def set_metrics(self, data: dict) -> None:
        self.metrics_json = json.dumps(data, ensure_ascii=False)

    def get_product(self) -> dict:
        return json.loads(self.product_json)


class AgentMemoryORM(Base):
    """
    Lightweight index of which ChromaDB collection holds
    each agent's embedding memory, keyed by simulation_id + agent_id.
    """

    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    simulation_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(50), nullable=False)
    chroma_collection: Mapped[str] = mapped_column(String(120), nullable=False)
    purchased: Mapped[bool] = mapped_column(default=False)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now
    )
