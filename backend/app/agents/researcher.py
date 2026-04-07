"""
Investigador (Researcher) — Advanced market research node for LaunchSim.

Implements three RAG enhancement techniques:
  1. Query Expansion   — The LLM expands the product concept into a rich search query.
  2. Multi-Query       — Generates 3 parallel search queries from different angles.
  3. Self-Reflective   — Evaluates result relevance (score 1-5) and retries if too low.
"""
from __future__ import annotations

import logging
import json
import concurrent.futures

from ddgs import DDGS
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import SimulationState
from app.core.llm import get_boost_llm

logger = logging.getLogger(__name__)

# ─────────────────────────── Prompts ────────────────────────────

QUERY_EXPANSION_PROMPT = """\
You are a market research specialist. Given a product concept, generate exactly 3 different
search queries that together cover:
  - Direct competitors and alternatives
  - Target audience complaints and unmet needs
  - Pricing landscape and willingness to pay

Return ONLY a JSON array of 3 strings. No explanation, no preamble.
Example: ["query one", "query two", "query three"]
"""

QUALITY_CHECK_PROMPT = """\
You are a critic evaluating the usefulness of web search results for market research.
Given a set of search results about a product/market, rate their usefulness on a scale of 1–5:
  1 = Completely irrelevant or empty
  3 = Partially useful, missing key competitive or demographic insights
  5 = Excellent: clearly identifies competitors, pricing, and customer pain points

Return ONLY a JSON object: {"score": <int>, "reason": "<one sentence>"}
"""

SYNTHESIS_PROMPT = """\
You are an expert market analyst preparing a briefing for a product launch simulation.
Your job: synthesize the provided web search results into a concise Market Research Context.

Structure your output in exactly 3 paragraphs:
  Paragraph 1 — Competitive Landscape: key competitors and substitute products.
  Paragraph 2 — Audience Pain Points: what the target audience struggles with today.
  Paragraph 3 — Pricing & Willingness to Pay: price sensitivity and benchmarks found.

Be specific, cite data points from the results where available. No preamble.
"""

REFINEMENT_PROMPT = """\
The initial web search results were rated low quality for market research.
Based on the product concept below, generate 3 NEW, more specific search queries.
Focus on finding real customer reviews, pricing data, and competitor comparisons.

Return ONLY a JSON array of 3 strings.
"""


# ─────────────────────── Helper functions ───────────────────────

def _run_search(query: str, max_results: int = 5) -> list[dict]:
    """Execute a single DuckDuckGo search and return results list."""
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        logger.warning("[Investigador] Search query failed ('%s'): %s", query, exc)
        return []


def _multi_query_search(queries: list[str]) -> list[dict]:
    """Run multiple search queries in parallel, deduplicate by URL/title."""
    all_results: list[dict] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(_run_search, q): q for q in queries}
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())

    # Deduplicate by href (URL)
    seen_urls: set[str] = set()
    unique_results: list[dict] = []
    for r in all_results:
        url = r.get("href", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    logger.info(
        "[Investigador] Multi-query returned %d unique results (from %d total).",
        len(unique_results),
        len(all_results),
    )
    return unique_results


def _format_results(results: list[dict]) -> str:
    """Convert raw DDGS result dicts to a readable text block."""
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        body = r.get("body", "")
        url = r.get("href", "")
        lines.append(f"[{i}] {title}\n    {body[:300]}\n    Source: {url}")
    return "\n\n".join(lines)


def _llm_json_call(llm, system: str, user: str, fallback: dict | list) -> dict | list:
    """Call LLM and attempt JSON parse; return fallback on failure."""
    try:
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        raw = resp.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw.strip())
    except Exception as exc:
        logger.warning("[Investigador] JSON parse failed: %s", exc)
        return fallback


# ────────────────────────── Main node ───────────────────────────

def researcher_node(state: SimulationState) -> SimulationState:
    """
    LangGraph node: Advanced market research with Multi-Query + Self-Reflective RAG.

    Pipeline:
      Step 1 — Query Expansion: LLM generates 3 rich search queries.
      Step 2 — Multi-Query Search: Run all 3 queries in parallel, deduplicate.
      Step 3 — Quality Check (Self-Reflective): Score result quality (1-5).
                If score < 3, regenerate queries and retry once.
      Step 4 — Contextual Synthesis: LLM synthesizes into 3-paragraph briefing.
    """
    product = state["product"]
    logger.info("[Investigador] Starting advanced market research for: %s", product.name)

    llm = get_boost_llm(temperature=0.4)

    # ── Step 1: Query Expansion ──────────────────────────────────
    logger.info("[Investigador] Step 1/4 — Query Expansion...")
    expansion_user = (
        f"Product: {product.name}\n"
        f"Description: {product.description}\n"
        f"Target Market: {product.target_market or 'General consumers'}\n\n"
        "Generate 3 search queries as instructed."
    )
    queries: list[str] = _llm_json_call(
        llm,
        QUERY_EXPANSION_PROMPT,
        expansion_user,
        fallback=[
            f"{product.name} competitors alternatives",
            f"{product.target_market or 'consumer'} complaints problems",
            f"{product.name} pricing review",
        ],
    )
    logger.info("[Investigador] Expanded queries: %s", queries)

    # ── Step 2: Multi-Query Search ───────────────────────────────
    logger.info("[Investigador] Step 2/4 — Multi-Query parallel search...")
    results = _multi_query_search(queries)

    if not results:
        logger.warning("[Investigador] All searches returned empty. Using fallback context.")
        return {
            **state,
            "market_research": (
                f"No live data available. Simulation will rely on intrinsic LLM knowledge "
                f"about the {product.name} market."
            ),
            "error": None,
        }

    formatted = _format_results(results)

    # ── Step 3: Self-Reflective Quality Check ────────────────────
    logger.info("[Investigador] Step 3/4 — Self-Reflective quality check...")
    quality_user = (
        f"Product: {product.name}\n\n"
        f"Search Results:\n{formatted[:2000]}\n\n"
        "Rate the quality of these results for market research purposes."
    )
    quality: dict = _llm_json_call(
        llm,
        QUALITY_CHECK_PROMPT,
        quality_user,
        fallback={"score": 3, "reason": "Could not evaluate quality."},
    )
    score = quality.get("score", 3)
    reason = quality.get("reason", "N/A")
    logger.info("[Investigador] Quality score: %d/5 — %s", score, reason)

    # If quality is poor, retry with refined queries (one retry max)
    if score < 3:
        logger.info("[Investigador] Low quality detected, refining queries and retrying...")
        refinement_user = (
            f"Product: {product.name}\n"
            f"Description: {product.description}\n"
            f"Previous failed queries: {queries}\n"
            f"Reason quality was low: {reason}\n\n"
            "Generate 3 better search queries."
        )
        refined_queries: list[str] = _llm_json_call(
            llm,
            REFINEMENT_PROMPT,
            refinement_user,
            fallback=[
                f"\"{product.name}\" user review",
                f"{product.name} vs competitors price comparison",
                f"best {product.target_market or 'consumer'} apps 2024",
            ],
        )
        logger.info("[Investigador] Refined queries: %s", refined_queries)
        retry_results = _multi_query_search(refined_queries)
        if retry_results:
            results = (results + retry_results)
            # Deduplicate again
            seen: set[str] = set()
            deduped: list[dict] = []
            for r in results:
                u = r.get("href", "")
                if u not in seen:
                    seen.add(u)
                    deduped.append(r)
            results = deduped
            formatted = _format_results(results)
            logger.info("[Investigador] Retry added results. Total unique: %d", len(results))

    # ── Step 4: Synthesis ────────────────────────────────────────
    logger.info("[Investigador] Step 4/4 — Synthesizing market context...")
    synthesis_user = (
        f"Product: {product.name}\n"
        f"Description: {product.description}\n"
        f"Target Market: {product.target_market or 'General consumers'}\n\n"
        f"Web Search Results ({len(results)} sources):\n{formatted}\n\n"
        "Synthesize into the 3-paragraph Market Research Context as instructed."
    )

    try:
        resp = llm.invoke([SystemMessage(content=SYNTHESIS_PROMPT), HumanMessage(content=synthesis_user)])
        market_research = resp.content.strip()
        logger.info(
            "[Investigador] Market research synthesized (%d chars, %d sources).",
            len(market_research),
            len(results),
        )
    except Exception as exc:
        logger.warning("[Investigador] Synthesis LLM call failed: %s", exc)
        market_research = f"Raw research context ({len(results)} results):\n{formatted[:2000]}"

    return {**state, "market_research": market_research, "error": None}
