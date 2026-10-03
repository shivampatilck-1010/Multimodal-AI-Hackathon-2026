"""Course-aware retriever. Public interface used by the tutor, Member 3 and evaluation."""

from __future__ import annotations

from app.tutor.models import RetrievalFilters, RetrievedChunk
from app.tutor.providers.embeddings import EmbeddingProvider
from app.tutor.vector_store import VectorStore


class Retriever:
    def __init__(self, store: VectorStore, embedder: EmbeddingProvider, default_top_k: int = 6) -> None:
        self.store = store
        self.embedder = embedder
        self.default_top_k = default_top_k

    def retrieve(
        self,
        course_id: str,
        query: str,
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
        min_score: float | None = None,
    ) -> list[RetrievedChunk]:
        """Return the top-k chunks of ``course_id`` most similar to ``query``.

        * Only the given course's partition is searched (no cross-course leakage).
        * ``filters`` are hard metadata constraints applied before ranking.
        * ``min_score`` optionally drops low-similarity chunks.
        * Output is deterministic: score desc, then chunk id.
        * Chunks with non-positive similarity are never returned.
        """
        query = query.strip()
        if not query:
            return []
        k = top_k or self.default_top_k
        vector = self.embedder.embed_query(query)
        hits = self.store.query(course_id, vector, k, filters.matches if filters else None)
        floor = 0.0 if min_score is None else min_score
        return [
            RetrievedChunk.from_unit(unit, score)
            for unit, score in hits
            if score > 0.0 and score >= floor
        ]

    def retrieve_multi(
        self,
        course_id: str,
        queries: list[str],
        top_k: int | None = None,
        filters: RetrievalFilters | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve for several phrasings and merge by max score (used for follow-ups)."""
        best: dict[str, RetrievedChunk] = {}
        for q in dict.fromkeys(q for q in queries if q.strip()):
            for chunk in self.retrieve(course_id, q, top_k, filters):
                prev = best.get(chunk.chunk_id)
                if prev is None or chunk.score > prev.score:
                    best[chunk.chunk_id] = chunk
        ranked = sorted(best.values(), key=lambda c: (-c.score, c.chunk_id))
        return ranked[: top_k or self.default_top_k]
