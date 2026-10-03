"""Storage and indexing for extracted diagrams, figures, and visual assets."""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

from PIL import Image

from app.kb.models import FigureUnit

logger = logging.getLogger(__name__)


class MediaStore:
    """Manages saved diagrams/figures and visual metadata."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self._figures: dict[str, dict[str, FigureUnit]] = {}  # course_id -> {figure_id -> FigureUnit}
        self._lock = threading.RLock()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._load_all()

    def save_image(
        self,
        course_id: str,
        figure_id: str,
        image: Image.Image,
        image_format: str = "PNG",
    ) -> str:
        """Save a PIL image to disk and return relative path."""
        course_dir = self.base_dir / course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        ext = image_format.lower()
        if ext == "jpeg":
            ext = "jpg"
        filename = f"{figure_id}.{ext}"
        filepath = course_dir / filename
        image.save(filepath, format=image_format)
        rel_path = f"{course_id}/{filename}"
        return rel_path

    def add_figure(self, figure: FigureUnit) -> None:
        """Add or update figure unit metadata."""
        with self._lock:
            course_figures = self._figures.setdefault(figure.course_id, {})
            course_figures[figure.id] = figure
            self._save_course(figure.course_id)

    def add_figures(self, figures: list[FigureUnit]) -> int:
        if not figures:
            return 0
        with self._lock:
            by_course: set[str] = set()
            for fig in figures:
                course_figures = self._figures.setdefault(fig.course_id, {})
                course_figures[fig.id] = fig
                by_course.add(fig.course_id)
            for cid in by_course:
                self._save_course(cid)
            return len(figures)

    def get_figure(self, course_id: str, figure_id: str) -> FigureUnit | None:
        with self._lock:
            return self._figures.get(course_id, {}).get(figure_id)

    def list_figures(self, course_id: str) -> list[FigureUnit]:
        with self._lock:
            return list(self._figures.get(course_id, {}).values())

    def get_figures_for_concept(self, course_id: str, concept: str) -> list[FigureUnit]:
        with self._lock:
            cf = self._figures.get(course_id, {})
            c_norm = concept.strip().casefold()
            return [
                fig
                for fig in cf.values()
                if any(c.strip().casefold() == c_norm for c in fig.associated_concepts)
            ]

    def get_image_path(self, rel_path: str) -> Path:
        return self.base_dir / rel_path

    def _save_course(self, course_id: str) -> None:
        course_dir = self.base_dir / course_id
        course_dir.mkdir(parents=True, exist_ok=True)
        target = course_dir / "figures.json"
        tmp = target.with_suffix(".tmp")
        figs = list(self._figures.get(course_id, {}).values())
        tmp.write_text(
            json.dumps([f.model_dump(mode="json") for f in figs], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(target)

    def _load_all(self) -> None:
        for course_dir in self.base_dir.iterdir():
            if course_dir.is_dir():
                fig_file = course_dir / "figures.json"
                if fig_file.exists():
                    try:
                        raw = json.loads(fig_file.read_text(encoding="utf-8"))
                        figs = [FigureUnit.model_validate(r) for r in raw]
                        self._figures[course_dir.name] = {f.id: f for f in figs}
                        logger.info(
                            "loaded_figures",
                            extra={"course_id": course_dir.name, "count": len(figs)},
                        )
                    except Exception as e:
                        logger.error(f"failed_loading_figures_{course_dir.name}: {e}")
