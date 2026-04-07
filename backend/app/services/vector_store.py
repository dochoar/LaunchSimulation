"""
ChromaDB service — persistent vector memory for simulated agents.

Each agent gets its own collection named:  sim_{simulation_id}_{agent_id}
Documents stored per agent:
  - bio / persona narrative
  - interaction reasoning
  - social posts content
"""
from __future__ import annotations

import chromadb
from chromadb.config import Settings

from app.core.config import settings


def _client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )


def collection_name(simulation_id: str, agent_id: str) -> str:
    # ChromaDB collection names: 3-63 chars, alphanumeric + underscores/hyphens
    sim_short = simulation_id.replace("-", "")[:12]
    return f"sim_{sim_short}_{agent_id}"


def upsert_agent_memory(
    simulation_id: str,
    agent_id: str,
    documents: list[str],
    metadatas: list[dict] | None = None,
    ids: list[str] | None = None,
) -> str:
    """Store documents into the agent's ChromaDB collection. Returns collection name."""
    client = _client()
    cname = collection_name(simulation_id, agent_id)
    col = client.get_or_create_collection(name=cname)

    _ids = ids or [f"{agent_id}_doc_{i}" for i in range(len(documents))]
    _metas = metadatas or [{"agent_id": agent_id, "sim_id": simulation_id}] * len(documents)

    col.upsert(documents=documents, metadatas=_metas, ids=_ids)
    return cname


def query_agent_memory(
    simulation_id: str,
    agent_id: str,
    query: str,
    n_results: int = 5,
) -> list[str]:
    """Retrieve top-k relevant documents from an agent's memory."""
    client = _client()
    cname = collection_name(simulation_id, agent_id)
    try:
        col = client.get_collection(name=cname)
    except Exception:
        return []

    results = col.query(query_texts=[query], n_results=n_results)
    docs = results.get("documents", [[]])[0]
    return docs


def delete_simulation_collections(simulation_id: str) -> None:
    """Clean up all agent collections for a simulation."""
    client = _client()
    sim_short = simulation_id.replace("-", "")[:12]
    prefix = f"sim_{sim_short}_"
    for col in client.list_collections():
        if col.name.startswith(prefix):
            client.delete_collection(col.name)
