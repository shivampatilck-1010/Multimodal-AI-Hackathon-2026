"""Provider factories: the only place that decides which concrete provider to use."""

from __future__ import annotations

import logging

from app.config import Settings
from app.tutor.providers.embeddings import (
    EmbeddingProvider,
    GeminiEmbeddingProvider,
    HashingEmbeddingProvider,
)
from app.tutor.providers.llm import (
    ExtractiveMockLLM,
    GeminiLLMProvider,
    LLMError,
    LLMMessage,
    LLMProvider,
)

logger = logging.getLogger(__name__)

__all__ = [
    "EmbeddingProvider",
    "LLMError",
    "LLMMessage",
    "LLMProvider",
    "build_embedding_provider",
    "build_llm_provider",
    "build_rewrite_llm_provider",
]


def _use_gemini(choice: str, settings: Settings, local_name: str) -> bool:
    if choice == "gemini":
        if not settings.has_gemini_key:
            raise RuntimeError(f"{choice} provider selected but GEMINI_API_KEY is not set")
        return True
    if choice == local_name:
        return False
    return settings.has_gemini_key  # auto


def build_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if _use_gemini(settings.embedding_provider, settings, "hashing"):
        assert settings.gemini_api_key is not None
        return GeminiEmbeddingProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_embedding_model,
            dim=settings.gemini_embedding_dim,
        )
    return HashingEmbeddingProvider()


def build_llm_provider(settings: Settings) -> LLMProvider:
    if _use_gemini(settings.llm_provider, settings, "mock"):
        assert settings.gemini_api_key is not None
        return GeminiLLMProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_chat_model,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return ExtractiveMockLLM()


def build_rewrite_llm_provider(settings: Settings) -> LLMProvider:
    if _use_gemini(settings.llm_provider, settings, "mock"):
        assert settings.gemini_api_key is not None
        return GeminiLLMProvider(
            api_key=settings.gemini_api_key.get_secret_value(),
            model=settings.gemini_rewrite_model,
            timeout_seconds=min(settings.llm_timeout_seconds, 20.0),
        )
    return ExtractiveMockLLM()
