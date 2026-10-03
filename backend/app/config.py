"""Application settings, loaded from environment variables / .env (never hard-coded)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(REPO_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: Literal["development", "production", "test"] = "development"

    # --- Providers -------------------------------------------------------
    gemini_api_key: SecretStr | None = None
    # "auto" = Gemini when GEMINI_API_KEY is set, otherwise deterministic local providers.
    llm_provider: Literal["auto", "gemini", "mock"] = "auto"
    embedding_provider: Literal["auto", "gemini", "hashing"] = "auto"
    gemini_chat_model: str = "gemini-3.8-flash"
    gemini_rewrite_model: str = "gemini-3.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dim: int = Field(default=768, ge=128, le=3072)
    llm_timeout_seconds: float = Field(default=60.0, gt=0)

    # --- Retrieval / grounding -------------------------------------------
    retrieval_top_k: int = Field(default=6, ge=1, le=50)
    # Minimum cosine similarity for a chunk to count as evidence. When unset the
    # embedding provider's calibrated default is used (see providers/embeddings.py).
    grounding_min_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    grounding_min_chunks: int = Field(default=1, ge=1, le=20)
    # Fraction of the query's content terms that must appear in the evidence.
    # 0 disables the lexical check (recommended for semantic embeddings).
    grounding_min_term_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    max_evidence_chunks: int = Field(default=6, ge=1, le=20)

    # --- Conversation ----------------------------------------------------
    history_max_turns: int = Field(default=6, ge=0, le=50)
    query_rewrite_enabled: bool = True
    allow_outside_knowledge: bool = False

    # --- Storage ---------------------------------------------------------
    data_dir: Path = BACKEND_DIR / "data" / "runtime"
    seed_file: Path | None = BACKEND_DIR / "data" / "sample_course.json"
    seed_on_startup: bool = True
    persist: bool = True

    # --- HTTP / security -------------------------------------------------
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit_per_minute: int = Field(default=30, ge=0)
    max_message_chars: int = Field(default=2000, ge=1, le=20_000)
    kb_ingest_token: SecretStr | None = None
    source_link_template: str = "/courses/{course_id}/sources/{source_id}"

    # --- Observability ---------------------------------------------------
    log_level: str = "INFO"
    log_query_text: bool | None = None  # default: only in development
    enable_debug: bool | None = None  # default: only in development

    @property
    def is_dev(self) -> bool:
        return self.app_env in ("development", "test")

    @property
    def debug_enabled(self) -> bool:
        return self.is_dev if self.enable_debug is None else self.enable_debug

    @property
    def should_log_query_text(self) -> bool:
        return self.is_dev if self.log_query_text is None else self.log_query_text

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def has_gemini_key(self) -> bool:
        return bool(self.gemini_api_key and self.gemini_api_key.get_secret_value().strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
