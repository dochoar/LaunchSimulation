"""
Ensamblaje del grafo LangGraph para LaunchSim.

Flujo:
  START → ethnographer → populator → launcher → conversador → chronicler → END

Si un nodo registra un error crítico (personas vacías), el grafo
hace cortocircuito hacia END para no ejecutar nodos dependientes con datos vacíos.
"""
from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.agents.chronicler import chronicler_node
from app.agents.conversador import conversador_node
from app.agents.ethnographer import ethnographer_node
from app.agents.launcher import launcher_node
from app.agents.populator import populator_node
from app.agents.researcher import researcher_node
from app.agents.state import SimulationState

logger = logging.getLogger(__name__)


def _should_continue_after_ethnographer(state: SimulationState) -> str:
    """Short-circuit if the Ethnographer produced no personas."""
    if not state.get("personas"):
        logger.error("[Graph] Ethnographer produced no personas — aborting.")
        return "end"
    return "populator"


def _should_continue_after_launcher(state: SimulationState) -> str:
    """Short-circuit if no interactions were generated."""
    if not state.get("interactions"):
        logger.error("[Graph] Launcher produced no interactions — aborting.")
        return "end"
    return "conversador"


def build_simulation_graph() -> StateGraph:
    """Build and compile the LaunchSim LangGraph workflow."""
    workflow = StateGraph(SimulationState)

    workflow.add_node("researcher", researcher_node)
    workflow.add_node("ethnographer", ethnographer_node)
    workflow.add_node("populator", populator_node)
    workflow.add_node("launcher", launcher_node)
    workflow.add_node("conversador", conversador_node)
    workflow.add_node("chronicler", chronicler_node)

    # Entry
    workflow.add_edge(START, "researcher")
    workflow.add_edge("researcher", "ethnographer")

    # Conditional edges with error guards
    workflow.add_conditional_edges(
        "ethnographer",
        _should_continue_after_ethnographer,
        {"populator": "populator", "end": END},
    )
    workflow.add_edge("populator", "launcher")

    workflow.add_conditional_edges(
        "launcher",
        _should_continue_after_launcher,
        {"conversador": "conversador", "end": END},
    )
    workflow.add_edge("conversador", "chronicler")
    workflow.add_edge("chronicler", END)

    return workflow.compile()


# Module-level compiled graph (singleton)
simulation_graph = build_simulation_graph()
