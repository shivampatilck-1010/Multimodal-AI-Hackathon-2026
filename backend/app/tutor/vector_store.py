"""Vector store abstraction + a simple, deterministic in-memory implementation.

Course isolation is structural: vectors are partitioned per ``course_id`` and a
query can only ever scan the partition of the course it was issued for.
Swap in Chroma / pgvector / Vertex Vector Search by implementing ``VectorStore``.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from app.tutor.models import ContentUnit


class VectorStore(Protocol):
    def upsert(self, units: list[ContentUnit], vectors: list[np.ndarray]) -> None: ...

    def delete(self, course_id: str, ids: list[str] | None = None) -> int: ...

    def query(
        self,
        course_id: str,
        vector: np.ndarray,
        top_k: int,
        predicate: Callable[[ContentUnit], bool] | None = None,
    ) -> list[tuple[ContentUnit, float]]: ...

    def get(self, course_id: str, unit_id: str) -> ContentUnit | None: ...

    def get_vector(self, course_id: str, unit_id: str) -> np.ndarray | None: ...

    def list_units(self, course_id: str) -> list[ContentUnit]: ...

    def courses(self) -> dict[str, int]: ...


@dataclass
class _Partition:
    units: dict[str, ContentUnit] = field(default_factory=dict)
    vectors: dict[str, np.ndarray] = field(default_factory=dict)
    _matrix: np.ndarray | None = None
    _order: list[str] = field(default_factory=list)

    def invalidate(self) -> None:
        self._matrix = None

    def matrix(self) -> tuple[list[str], np.ndarray]:
        if self._matrix is None:
            self._order = sorted(self.units)  # deterministic order
            self._matrix = (
                np.vstack([self.vectors[i] for i in self._order]).astype(np.float32)
                if self._order
                else np.zeros((0, 0), dtype=np.float32)
            )
        return self._order, self._matrix


class InMemoryVectorStore:
    """Exact cosine search over L2-normalised vectors. Fine for hackathon-scale courses."""

    def __init__(self) -> None:
        self._partitions: dict[str, _Partition] = {}
        self._lock = threading.RLock()

    def upsert(self, units: list[ContentUnit], vectors: list[np.ndarray]) -> None:
        if len(units) != len(vectors):
            raise ValueError("units and vectors must have the same length")
        with self._lock:
            for unit, vec in zip(units, vectors, strict=True):
                part = self._partitions.setdefault(unit.course_id, _Partition())
                part.units[unit.id] = unit
                part.vectors[unit.id] = np.asarray(vec, dtype=np.float32)
                part.invalidate()

    def delete(self, course_id: str, ids: list[str] | None = None) -> int:
        with self._lock:
            part = self._partitions.get(course_id)
            if part is None:
                return 0
            if ids is None:
                removed = len(part.units)
                del self._partitions[course_id]
                return removed
            removed = 0
            for unit_id in ids:
                if part.units.pop(unit_id, None) is not None:
                    part.vectors.pop(unit_id, None)
                    removed += 1
            part.invalidate()
            return removed

    def query(
        self,
        course_id: str,
        vector: np.ndarray,
        top_k: int,
        predicate: Callable[[ContentUnit], bool] | None = None,
    ) -> list[tuple[ContentUnit, float]]:
        with self._lock:
            part = self._partitions.get(course_id)
            if part is None or not part.units or top_k <= 0:
                return []
            order, matrix = part.matrix()
            if matrix.shape[1] != vector.shape[0]:
                raise ValueError("Query vector dimension does not match the index")
            scores = matrix @ vector.astype(np.float32)
            results: list[tuple[ContentUnit, float]] = []
            for idx in range(len(order)):
                unit = part.units[order[idx]]
                if predicate is None or predicate(unit):
                    results.append((unit, float(scores[idx])))
        # Highest score first; ties broken by id for deterministic output.
        results.sort(key=lambda r: (-round(r[1], 6), r[0].id))
        return results[:top_k]

    def get(self, course_id: str, unit_id: str) -> ContentUnit | None:
        with self._lock:
            part = self._partitions.get(course_id)
            return part.units.get(unit_id) if part else None

    def get_vector(self, course_id: str, unit_id: str) -> np.ndarray | None:
        with self._lock:
            part = self._partitions.get(course_id)
            return part.vectors.get(unit_id) if part else None

    def list_units(self, course_id: str) -> list[ContentUnit]:
        with self._lock:
            part = self._partitions.get(course_id)
            return [part.units[i] for i in sorted(part.units)] if part else []

    def courses(self) -> dict[str, int]:
        with self._lock:
            return {cid: len(p.units) for cid, p in sorted(self._partitions.items())}
