"""
Agente Entrevistador — interfaz de chat RAG para hablar con un agente simulado.

Flujo por pregunta:
  1. Recupera los chunks más relevantes de ChromaDB para ese agent_id
  2. Busca la interacción y el post social del agente en el historial
  3. Construye un prompt con todo el contexto
  4. El LLM responde EN PRIMERA PERSONA como ese agente
"""
from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.models.schemas import (
    AgentInteractionEvent,
    InterviewResponse,
    SimulatedAgentProfile,
    SocialPost,
)
from app.services.vector_store import query_agent_memory

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are roleplaying as a specific consumer persona in a product launch simulation.
You MUST answer in first person, staying completely in character.
Your answers must be consistent with your profile, pain points, income, and the
action you took (whether you bought, ignored, or abandoned the product).
Be specific — reference your occupation, location, and real-life context.
Never break character. Never mention that you are an AI or a simulation.
Answer in the same language the user asks in.
"""


def interview_agent(
    simulation_id: str,
    persona: SimulatedAgentProfile,
    interaction: AgentInteractionEvent | None,
    social_post: SocialPost | None,
    question: str,
) -> InterviewResponse:
    """
    Run a single RAG-powered interview turn for one simulated agent.
    Returns an InterviewResponse with the agent's in-character answer.
    """
    llm = get_llm(temperature=0.75)

    # --- RAG: retrieve relevant memory chunks ---
    memory_docs = query_agent_memory(
        simulation_id=simulation_id,
        agent_id=persona.agent_id,
        query=question,
        n_results=4,
    )
    memory_context = "\n".join(f"- {doc}" for doc in memory_docs) if memory_docs else "No additional context."

    # --- Interaction summary ---
    if interaction:
        action_summary = (
            f"Action taken: {interaction.interaction_type.value}. "
            f"Reasoning at the time: {interaction.reasoning}"
        )
        purchased = interaction.interaction_type.value == "purchased"
    else:
        action_summary = "No interaction recorded."
        purchased = False

    # --- Social post context ---
    post_context = (
        f"You posted on {social_post.platform}: \"{social_post.content}\""
        if social_post
        else "You did not post publicly about this product."
    )

    # --- Construct the full prompt ---
    persona_block = (
        f"YOUR IDENTITY:\n"
        f"Name: {persona.name}\n"
        f"Age: {persona.age} | Gender: {persona.gender} | Location: {persona.location}\n"
        f"Occupation: {persona.occupation} | Income: ~${persona.annual_income_usd:,.0f}/year\n"
        f"Archetype: {persona.archetype.value} | Tech savviness: {persona.tech_savviness}/10\n"
        f"Pain points: {', '.join(pp.topic for pp in persona.pain_points)}\n"
        f"Goals: {', '.join(persona.goals)}\n"
        f"Cognitive biases: {', '.join(persona.cognitive_biases)}\n"
        f"Willingness to pay: ${persona.willingness_to_pay_usd:.2f}\n"
        f"Bio: {persona.bio}\n\n"
        f"YOUR INTERACTION WITH THE PRODUCT:\n{action_summary}\n\n"
        f"YOUR PUBLIC REACTION:\n{post_context}\n\n"
        f"RELEVANT MEMORIES:\n{memory_context}"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"{persona_block}\n\n---\nQuestion from researcher: {question}"),
    ]

    try:
        resp = llm.invoke(messages)
        answer = resp.content.strip()
    except Exception as exc:
        logger.error("[Entrevistador] LLM call failed for %s: %s", persona.agent_id, exc)
        answer = "I'm not able to answer right now."

    reasoning_summary = (
        f"{persona.name} {'purchased' if purchased else 'did not purchase'} the product. "
        f"{interaction.reasoning if interaction else ''}"
    ).strip()

    return InterviewResponse(
        agent_id=persona.agent_id,
        agent_name=persona.name,
        answer=answer,
        purchased=purchased,
        reasoning_summary=reasoning_summary,
    )
