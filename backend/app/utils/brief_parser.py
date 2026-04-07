"""
brief_parser.py — Convierte un product brief en texto libre a ProductInput.

Usa el LLM configurado para extraer los campos estructurados. Soporta cualquier
formato de brief (markdown, PDF exportado, deck de texto, etc.).
"""
from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm
from app.models.schemas import Channel, ProductInput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a product analyst. Extract structured data from a product brief.
Output ONLY valid JSON. No markdown, no explanation. Start with { and end with }.

Required fields:
{
  "name": "Product name (string)",
  "description": "Full description combining problem, solution, and differentiators (300-600 chars)",
  "price_usd": <primary price as float — use hardware price if both hardware+subscription exist>,
  "channel": one of ["social_media", "email", "paid_ads", "seo", "word_of_mouth", "app_store", "other"],
  "target_market": "Concise description of the target audience (100-200 chars)"
}

Rules:
- price_usd must be a positive number. If range given (e.g. $5-8), use the midpoint.
- For channel: map "TechCrunch/press/media" → "social_media", "App Store" → "app_store",
  "ProductHunt/direct web" → "other", "paid advertising" → "paid_ads".
- description must capture the core value proposition and key differentiators.
- If a field cannot be determined, use a sensible default.
"""

USER_PROMPT_TEMPLATE = """\
Product brief:
---
{brief_text}
---

Extract the structured product data as JSON.
"""


def parse_brief(brief_text: str, num_agents: int = 10) -> ProductInput:
    """
    Parse a free-text product brief into a ProductInput.

    Args:
        brief_text: Raw text of the product brief (markdown, plain text, etc.)
        num_agents: Number of personas to generate in the simulation.

    Returns:
        ProductInput ready to be passed to the simulation pipeline.

    Raises:
        ValueError: If the LLM output cannot be parsed after retries.
    """
    llm = get_llm(temperature=0.1)  # Low temp for deterministic extraction
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=USER_PROMPT_TEMPLATE.format(brief_text=brief_text[:4000])),
    ]

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            resp = llm.invoke(messages)
            data = _extract_json(resp.content)
            return _build_product_input(data, num_agents)
        except Exception as exc:
            logger.warning("[BriefParser] Attempt %d failed: %s", attempt + 1, exc)
            last_error = exc

    raise ValueError(f"Could not parse brief after 3 attempts: {last_error}")


def parse_brief_from_file(path: str, num_agents: int = 10) -> ProductInput:
    """Load a brief from a file path and parse it."""
    with open(path, encoding="utf-8") as f:
        brief_text = f.read()
    logger.info("[BriefParser] Loaded brief from %s (%d chars)", path, len(brief_text))
    return parse_brief(brief_text, num_agents=num_agents)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise ValueError(f"No JSON object found in LLM response: {text[:200]}")


def _build_product_input(data: dict, num_agents: int) -> ProductInput:
    # Normalize channel
    try:
        channel = Channel(data.get("channel", "other"))
    except ValueError:
        channel = Channel.other

    return ProductInput(
        name=str(data["name"]),
        description=str(data["description"]),
        price_usd=float(data["price_usd"]),
        channel=channel,
        target_market=str(data.get("target_market", "")),
        num_agents=num_agents,
    )
