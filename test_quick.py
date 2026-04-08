#!/usr/bin/env python3
"""
Prueba rápida: corre researcher + ethnographer con 3 personas.
Ejecutar desde: /home/david/LaunchSimulation/backend/
  python ../test_quick.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

from app.agents.researcher import researcher_node
from app.agents.ethnographer import ethnographer_node
from app.models.schemas import ProductInput, Channel

# ── Producto de prueba ────────────────────────────────────────────
product = ProductInput(
    name="QuickNote AI",
    description=(
        "A mobile app that records voice memos and instantly transcribes them "
        "with AI-generated summaries and action items. Targets busy professionals "
        "who take lots of meetings and struggle to keep notes organized."
    ),
    price_usd=9.99,
    channel=Channel.app_store,
    target_market="Busy professionals aged 25-45",
    num_agents=10,  # mínimo permitido por el schema
)

state = {
    "simulation_id": "test-001",
    "product": product,
    "market_research": None,
    "personas": [],
    "populated_agent_ids": [],
    "interactions": [],
    "social_posts": [],
    "metrics": None,
    "error": None,
}

# ── Nodo 1: Researcher ────────────────────────────────────────────
print("=" * 60)
print("  NODO 1: Researcher (búsqueda de mercado)")
print("=" * 60)
state = researcher_node(state)
research = state.get("market_research", "")
print(research[:600], "..." if len(research) > 600 else "")

# ── Nodo 2: Ethnographer ──────────────────────────────────────────
print("\n" + "=" * 60)
print("  NODO 2: Ethnographer (generando 3 personas)")
print("=" * 60)
state = ethnographer_node(state)

for p in state.get("personas", []):
    print(f"\n  {p.agent_id}  {p.name:<22} {p.archetype.value:<16} WTP=${p.willingness_to_pay_usd:.0f}")
    print(f"           {p.bio[:90]}...")

print("\n  Error:", state.get("error"))
print("=" * 60)
print(f"  Personas generadas: {len(state.get('personas', []))}/3")
print("=" * 60)
