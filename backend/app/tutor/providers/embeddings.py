"""Embedding providers.

All provider-specific code lives here, behind the ``EmbeddingProvider`` protocol.
The rest of the application only calls ``embed_query`` / ``embed_documents``.
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import Protocol, runtime_checkable

import numpy as np

from app.tutor.text import content_terms

logger = logging.getLogger(__name__)


@runtime_checkable
class EmbeddingProvider(Protocol):
    name: str
    #: Stable identifier of the vector space (model + dimension). Vectors from
    #: different signatures must never be compared.
    signature: str
    #: Calibrated default for GROUNDING_MIN_SCORE with this provider.
    default_min_score: float

    def embed_query(self, text: str) -> np.ndarray: ...

    def embed_documents(self, texts: list[str]) -> list[np.ndarray]: ...


def _l2_normalize(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    return vec if norm == 0.0 else vec / norm


class HashingEmbeddingProvider:
    """Deterministic, offline lexical embedding (feature hashing of unigrams + bigrams).

    Used for tests, CI and local development without an API key. It is purely
    lexical, so its cosine scores are lower than semantic embeddings; the
    calibrated grounding threshold reflects that.
    """

    name = "hashing"
    default_min_score = 0.15

    def __init__(self, dim: int = 1024) -> None:
        self.dim = dim
        self.signature = f"hashing-v1-{dim}"

    def _bucket(self, feature: str) -> tuple[int, float]:
        digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "little")
        return value % self.dim, (1.0 if (value >> 63) & 1 == 0 else -1.0)

    def _embed(self, text: str) -> np.ndarray:
        terms = content_terms(text)
        features = terms + [f"{a}_{b}" for a, b in zip(terms, terms[1:], strict=False)]
        counts: dict[str, int] = {}
        for f in features:
            counts[f] = counts.get(f, 0) + 1
        vec = np.zeros(self.dim, dtype=np.float32)
        for feature, count in counts.items():
            idx, sign = self._bucket(feature)
            vec[idx] += sign * (1.0 + math.log(count))
        return _l2_normalize(vec)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[np.ndarray]:
        return [self._embed(t) for t in texts]


class GeminiEmbeddingProvider:
    """Gemini embeddings via the official ``google-genai`` SDK."""

    name = "gemini"
    # Empirical starting point for gemini-embedding-001 cosine similarity.
    # Tune with the evaluation set (see docs/TUTOR.md, "Tuning the threshold").
    default_min_score = 0.65
    _BATCH = 100

    def __init__(self, api_key: str, model: str, dim: int) -> None:
        from google import genai  # imported lazily so tests never need the SDK/network

        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dim = dim
        self.signature = f"gemini-{model}-{dim}"

    def _embed(self, texts: list[str], task_type: str) -> list[np.ndarray]:
        from google.genai import types

        out: list[np.ndarray] = []
        for start in range(0, len(texts), self._BATCH):
            batch = texts[start : start + self._BATCH]
            response = self._client.models.embed_content(
                model=self._model,
                contents=batch,
                config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self._dim),
            )
            for emb in response.embeddings or []:
                # Truncated (non-3072) Gemini embeddings must be re-normalised.
                out.append(_l2_normalize(np.asarray(emb.values, dtype=np.float32)))
        if len(out) != len(texts):
            raise RuntimeError("Embedding provider returned an unexpected number of vectors")
        return out

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text], "RETRIEVAL_QUERY")[0]

    def embed_documents(self, texts: list[str]) -> list[np.ndarray]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT") if texts else []
