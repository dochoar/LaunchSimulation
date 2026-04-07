"""
Etnógrafo — Genera N personas detalladas a partir de la descripción del producto.

Adaptado para modelos locales 7B (qwen2.5:7b vía Ollama):
  - Genera en LOTES de 8 personas por llamada (evita superar el contexto útil del modelo)
  - Incluye reparación de JSON robusta para manejar preambles y formato inconsistente
  - Reintenta hasta 2 veces por lote antes de descartar y continuar
"""
from __future__ import annotations

import json
import logging
import re
import time

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import SimulationState
from app.core.llm import get_boost_llm
from app.models.schemas import Archetype, Channel, PainPoint, SimulatedAgentProfile

logger = logging.getLogger(__name__)

BATCH_SIZE = 8  # Keep batches small — 7B models handle ~8 personas reliably

SYSTEM_PROMPT = """\
You are a market research expert generating synthetic consumer personas.
Output ONLY a valid JSON array. No explanation, no markdown, no preamble.
Start your response with [ and end with ].
"""

USER_PROMPT_TEMPLATE = """\
Product: "{name}" — ${price_usd} USD — sold via {channel}
Description: {description}

Target market: {target_market}

Live Web Market Context & Competitors:
{market_research}

Generate exactly {count} consumer personas as a JSON array.
Each object must have these exact fields:
{{
  "agent_id": "agent_{start_idx:03d}" to "agent_{end_idx:03d}",
  "name": "Full Name",
  "age": <int 18-70>,
  "gender": "male|female|non-binary",
  "location": "City, Country",
  "occupation": "Job title",
  "annual_income_usd": <float>,
  "archetype": one of [{archetypes}],
  "tech_savviness": <int 1-10>,
  "pain_points": [{{"topic": "...", "intensity": <1-10>}}, {{"topic": "...", "intensity": <1-10>}}],
  "goals": ["goal 1", "goal 2"],
  "preferred_channels": [one or two of [{channels}]],
  "cognitive_biases": ["bias 1", "bias 2"],
  "willingness_to_pay_usd": <float>,
  "bio": "One sentence describing who this person is and their relationship with this type of product."
}}

Make the personas diverse: vary age, income, location, archetype, and opinion of the product.
Output ONLY the JSON array, nothing else.
"""


def _extract_json_array(text: str) -> list[dict] | None:
    """
    Robust extraction: handles markdown fences, leading text, and truncated arrays.
    Tries multiple strategies before giving up.
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Strategy 1: direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: find first [...] block
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 3: extract individual {...} objects and wrap in array
    objects = re.findall(r"\{[^{}]+\}", text, re.DOTALL)
    if objects:
        try:
            return [json.loads(o) for o in objects]
        except json.JSONDecodeError:
            pass

    return None


def _call_with_retry(llm, messages: list, retries: int = 2) -> list[dict]:
    for attempt in range(retries + 1):
        try:
            resp = llm.invoke(messages)
            result = _extract_json_array(resp.content)
            if result:
                return result
            logger.warning("[Etnógrafo] Attempt %d: could not parse JSON", attempt + 1)
        except Exception as exc:
            logger.warning("[Etnógrafo] Attempt %d failed: %s", attempt + 1, exc)
        if attempt < retries:
            time.sleep(1)
    return []


def ethnographer_node(state: SimulationState) -> SimulationState:
    """LangGraph node: generates all personas via LLM in small batches."""
    product = state["product"]
    total = product.num_agents
    logger.info("[Etnógrafo] Generating %d personas in batches of %d...", total, BATCH_SIZE)

    llm = get_boost_llm(temperature=0.85)
    archetypes = ", ".join(f'"{a.value}"' for a in Archetype)
    channels = ", ".join(f'"{c.value}"' for c in Channel)

    all_personas: list[SimulatedAgentProfile] = []
    idx = 1

    while idx <= total:
        count = min(BATCH_SIZE, total - idx + 1)
        start_idx = idx
        end_idx = idx + count - 1

        prompt = USER_PROMPT_TEMPLATE.format(
            name=product.name,
            price_usd=product.price_usd,
            channel=product.channel.value,
            description=product.description[:600],  # cap to preserve context budget
            target_market=product.target_market or "General consumer market",
            market_research=state.get("market_research", "No live context available."),
            count=count,
            start_idx=start_idx,
            end_idx=end_idx,
            archetypes=archetypes,
            channels=channels,
        )

        messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]
        raw_personas = _call_with_retry(llm, messages)

        parsed = 0
        for i, raw in enumerate(raw_personas):
            # Assign sequential agent_id regardless of what the model returned
            raw["agent_id"] = f"agent_{start_idx + i:03d}"
            try:
                all_personas.append(_parse_persona(raw))
                parsed += 1
            except Exception as exc:
                logger.warning("[Etnógrafo] Skipping malformed persona: %s", exc)

        logger.info("[Etnógrafo] Batch %d-%d: %d/%d parsed.", start_idx, end_idx, parsed, count)
        idx += count

    if not all_personas:
        return {**state, "personas": [], "error": "Ethnographer produced no valid personas."}

    logger.info("[Etnógrafo] Total: %d personas generated.", len(all_personas))
    return {**state, "personas": all_personas, "error": None}


def _parse_persona(data: dict) -> SimulatedAgentProfile:
    pain_points = [
        PainPoint(topic=pp["topic"], intensity=int(pp.get("intensity", 5)))
        for pp in data.get("pain_points", [])
        if isinstance(pp, dict) and "topic" in pp
    ]
    if not pain_points:
        pain_points = [PainPoint(topic="general friction", intensity=5)]

    try:
        archetype = Archetype(data.get("archetype", "pragmatist"))
    except ValueError:
        archetype = Archetype.pragmatist

    preferred_channels = []
    for ch in data.get("preferred_channels", []):
        try:
            preferred_channels.append(Channel(ch))
        except ValueError:
            pass

    return SimulatedAgentProfile(
        agent_id=data["agent_id"],
        name=str(data.get("name", f"Agent {data['agent_id']}")),
        age=int(data.get("age", 30)),
        gender=str(data.get("gender", "unspecified")),
        location=str(data.get("location", "Unknown")),
        occupation=str(data.get("occupation", "Professional")),
        annual_income_usd=float(data.get("annual_income_usd", 40000)),
        archetype=archetype,
        tech_savviness=int(data.get("tech_savviness", 5)),
        pain_points=pain_points,
        goals=list(data.get("goals", [])),
        preferred_channels=preferred_channels,
        cognitive_biases=list(data.get("cognitive_biases", [])),
        willingness_to_pay_usd=float(data.get("willingness_to_pay_usd", 0)),
        bio=str(data.get("bio", "")),
    )
