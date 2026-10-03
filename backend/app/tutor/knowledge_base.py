"""Knowledge base facade: the ingestion entry point for Member 1.

Member 1's pipeline (PDF / slide / video ingestion) should call
``KnowledgeBase.add_units(list[ContentUnit])`` (or ``POST /api/kb/units``).
The KB embeds units with the configured ``EmbeddingProvider`` and indexes them in
the ``VectorStore``. Units are persisted as JSON; vectors are cached per embedding
signature and transparently re-computed if the embedding model changes.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path

import numpy as np

from app.tutor.models import ContentUnit
from app.tutor.providers.embeddings import EmbeddingProvider
from app.tutor.vector_store import VectorStore

logger = logging.getLogger(__name__)


def embedding_text(unit: ContentUnit) -> str:
    """Text that gets embedded: topic/concept labels help retrieval of short chunks."""
    header = " | ".join(p for p in (unit.topic, unit.concept) if p)
    return f"{header}\n{unit.text}" if header else unit.text


class KnowledgeBase:
    def __init__(
        self,
        store: VectorStore,
        embedder: EmbeddingProvider,
        persist_dir: Path | None = None,
    ) -> None:
        self.store = store
        self.embedder = embedder
        self.persist_dir = persist_dir
        self._lock = threading.Lock()
        if persist_dir is not None:
            persist_dir.mkdir(parents=True, exist_ok=True)
            self._load()

    # ------------------------------------------------------------------ write
    def add_units(self, units: list[ContentUnit]) -> int:
        """Insert or replace content units (idempotent on ``(course_id, id)``)."""
        if not units:
            return 0
        seen: set[tuple[str, str]] = set()
        for u in units:
            key = (u.course_id, u.id)
            if key in seen:
                raise ValueError(f"Duplicate content unit id in batch: {u.course_id}/{u.id}")
            seen.add(key)
        vectors = self.embedder.embed_documents([embedding_text(u) for u in units])
        with self._lock:
            self.store.upsert(units, vectors)
            self._save()
        logger.info("kb_units_added", extra={"count": len(units)})
        return len(units)

    def delete_course(self, course_id: str) -> int:
        with self._lock:
            removed = self.store.delete(course_id)
            self._save()
        return removed

    # ------------------------------------------------------------------- read
    def get_unit(self, course_id: str, unit_id: str) -> ContentUnit | None:
        return self.store.get(course_id, unit_id)

    def list_units(self, course_id: str) -> list[ContentUnit]:
        return self.store.list_units(course_id)

    def courses(self) -> dict[str, int]:
        return self.store.courses()

    # ------------------------------------------------------------ persistence
    @property
    def _units_path(self) -> Path:
        assert self.persist_dir is not None
        return self.persist_dir / "units.json"

    @property
    def _vectors_path(self) -> Path:
        assert self.persist_dir is not None
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in self.embedder.signature)
        return self.persist_dir / f"vectors-{safe}.npz"

    def _all_units(self) -> list[ContentUnit]:
        return [u for cid in self.store.courses() for u in self.store.list_units(cid)]

    def _save(self) -> None:
        if self.persist_dir is None:
            return
        units = self._all_units()
        tmp = self._units_path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps([u.model_dump(mode="json") for u in units], ensure_ascii=False, indent=1),
            encoding="utf-8",
        )
        tmp.replace(self._units_path)
        if units:
            keys = np.array([f"{u.course_id}\x1f{u.id}" for u in units])
            vecs = np.vstack([self._vector_for(u) for u in units])
            np.savez(self._vectors_path, keys=keys, vectors=vecs)

    def _vector_for(self, unit: ContentUnit) -> np.ndarray:
        vec = self.store.get_vector(unit.course_id, unit.id)
        if vec is not None:
            return vec
        return self.embedder.embed_documents([embedding_text(unit)])[0]

    def _load(self) -> None:
        if not self._units_path.exists():
            return
        raw = json.loads(self._units_path.read_text(encoding="utf-8"))
        units = [ContentUnit.model_validate(r) for r in raw]
        if not units:
            return
        cached: dict[str, np.ndarray] = {}
        if self._vectors_path.exists():
            with np.load(self._vectors_path, allow_pickle=False) as data:
                cached = dict(zip(data["keys"].tolist(), data["vectors"], strict=True))
        missing = [u for u in units if f"{u.course_id}\x1f{u.id}" not in cached]
        if missing:
            logger.info("kb_reembedding", extra={"count": len(missing)})
            for u, v in zip(
                missing, self.embedder.embed_documents([embedding_text(u) for u in missing]), strict=True
            ):
                cached[f"{u.course_id}\x1f{u.id}"] = v
        self.store.upsert(units, [cached[f"{u.course_id}\x1f{u.id}"] for u in units])
        if missing:
            self._save()
        logger.info("kb_loaded", extra={"count": len(units)})
