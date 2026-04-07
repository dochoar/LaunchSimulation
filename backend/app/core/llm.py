"""
LLM factory — returns ChatOpenAI instances for standard and boost models.
Compatible with any OpenAI-API provider (OpenAI, Together, Groq, Ollama, etc.).
"""
from functools import lru_cache

from langchain_openai import ChatOpenAI

from app.core.config import settings


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.7) -> ChatOpenAI:
    """Standard model — used by Launcher, Conversador, Populator."""
    return ChatOpenAI(
        model=settings.llm_model_name,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        temperature=temperature,
    )


@lru_cache(maxsize=1)
def get_boost_llm(temperature: float = 0.8) -> ChatOpenAI:
    """
    High-capability model — used by Etnógrafo and Cronista where
    depth of reasoning matters more than speed.
    Falls back to the standard model if no boost key is configured.
    """
    api_key = settings.llm_boost_api_key or settings.llm_api_key
    base_url = settings.llm_boost_base_url or settings.llm_base_url
    model = settings.effective_boost_model

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=temperature,
    )
