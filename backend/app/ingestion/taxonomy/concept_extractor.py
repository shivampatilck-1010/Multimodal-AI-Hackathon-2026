"""Deterministic concept and taxonomy extraction for course content.

Builds concept nodes from existing ContentUnit objects, preserving unit IDs
and mapping every concept to its supporting content. Gemini is optional:
the deterministic extractor works without an API key.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any

from app.kb.models import ConceptNode, FigureUnit
from app.tutor.models import ContentUnit

logger = logging.getLogger(__name__)


class ConceptExtractor:
    """Extract topic-level concepts and link them to source content."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-3.8-flash",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self._client = None

        if api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=api_key)
            except Exception:
                logger.exception(
                    "Could not initialize Gemini client; "
                    "using deterministic taxonomy extraction."
                )

    @staticmethod
    def _slug(value: str) -> str:
        """Create a stable, URL-safe identifier component."""
        slug = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
        return slug or "general"

    @staticmethod
    def _clean(value: Any, fallback: str = "General Concepts") -> str:
        """Return a normalized, non-empty string."""
        if value is None:
            return fallback
        cleaned = re.sub(r"\s+", " ", str(value)).strip()
        return cleaned or fallback

    @staticmethod
    def _unit_sort_key(unit: ContentUnit) -> tuple[int, str]:
        """Sort units deterministically by source position, then ID."""
        source = unit.source
        if getattr(source, "type", None) == "pdf":
            position = getattr(source, "page", None)
        elif getattr(source, "type", None) == "slide":
            position = getattr(source, "slide", None)
        else:
            position = getattr(source, "start_seconds", None)

        try:
            numeric_position = int(position) if position is not None else 10**9
        except (TypeError, ValueError):
            numeric_position = 10**9

        return numeric_position, str(unit.id)

    @staticmethod
    def _summary_for_topic(topic: str, units: list[ContentUnit]) -> str:
        """Use source material to generate a useful evidence-grounded summary."""
        excerpts: list[str] = []
        seen: set[str] = set()

        for unit in units:
            text = re.sub(r"\s+", " ", str(unit.text)).strip()
            if text and text.casefold() not in seen:
                excerpts.append(text)
                seen.add(text.casefold())

        if not excerpts:
            return f"Study materials and key ideas related to {topic}."

        # A concise summary based on actual course content rather than a
        # fabricated generic definition.
        combined = " ".join(excerpts)
        if len(combined) > 700:
            combined = combined[:697].rsplit(" ", 1)[0] + "..."

        return combined

    def extract_taxonomy(
        self,
        course_id: str,
        units: list[ContentUnit],
        figures: list[FigureUnit] | None = None,
    ) -> tuple[list[ContentUnit], dict[str, ConceptNode], dict[str, dict[str, list[str]]]]:
        """Extract concepts, preserve units, and build a topic hierarchy.

        Returns:
            tagged_units:
                Existing units with topic/subtopic/concept fields preserved.
            nodes:
                Dictionary of concept ID -> ConceptNode.
            hierarchy:
                Dictionary mapping topic -> subtopic -> concept IDs.

        This method is deterministic and does not require Gemini.
        """
        figures = figures or []

        if not units:
            logger.warning("No content units provided for course %s", course_id)
            return [], {}, {}

        # Group by topic, using the existing content's labels first.
        # If a topic is missing, fall back to the unit's concept, then its ID.
        topic_units: dict[str, list[ContentUnit]] = defaultdict(list)

        for unit in units:
            if str(unit.course_id) != str(course_id):
                logger.warning(
                    "Skipping unit %s belonging to course %s, not %s",
                    unit.id,
                    unit.course_id,
                    course_id,
                )
                continue

            topic = self._clean(
                unit.topic or unit.concept or unit.subtopic,
                fallback="General Concepts",
            )
            topic_units[topic].append(unit)

        if not topic_units:
            return [], {}, {}

        figure_ids_by_topic: dict[str, list[str]] = defaultdict(list)
        for figure in figures:
            associated = getattr(figure, "associated_concepts", []) or []
            figure_topic = self._clean(
                getattr(figure, "topic", None)
                or getattr(figure, "concept", None),
                fallback="",
            )

            candidate_topics = {name.casefold(): name for name in topic_units}
            matched_topic = candidate_topics.get(figure_topic.casefold())

            if not matched_topic:
                for associated_name in associated:
                    matched_topic = candidate_topics.get(
                        str(associated_name).casefold()
                    )
                    if matched_topic:
                        break

            if matched_topic:
                figure_id = str(getattr(figure, "id", "")).strip()
                if figure_id and figure_id not in figure_ids_by_topic[matched_topic]:
                    figure_ids_by_topic[matched_topic].append(figure_id)

        nodes: dict[str, ConceptNode] = {}
        hierarchy: dict[str, dict[str, list[str]]] = {}
        tagged_units: list[ContentUnit] = []

        for topic in sorted(topic_units, key=str.casefold):
            topic_group = sorted(topic_units[topic], key=self._unit_sort_key)

            # Keep source-level subtopics in the hierarchy.
            subtopic_map: dict[str, list[str]] = defaultdict(list)
            concept_id = f"concept_{self._slug(topic)}"

            subtopics = sorted(
                {
                    self._clean(unit.subtopic, fallback="Key Concepts")
                    for unit in topic_group
                },
                key=str.casefold,
            )
            primary_subtopic = subtopics[0] if len(subtopics) == 1 else "Core Concepts"

            unit_ids = list(dict.fromkeys(str(unit.id) for unit in topic_group))
            figure_ids = list(figure_ids_by_topic.get(topic, []))

            node = ConceptNode(
                id=concept_id,
                course_id=course_id,
                name=topic,
                topic=topic,
                subtopic=primary_subtopic,
                summary=self._summary_for_topic(topic, topic_group),
                content_unit_ids=unit_ids,
                figure_ids=figure_ids,
                metadata={
                    "extraction_method": "deterministic",
                    "source_unit_count": len(unit_ids),
                    "source_subtopics": subtopics,
                },
            )
            nodes[concept_id] = node

            for subtopic in subtopics:
                subtopic_map[subtopic].append(concept_id)

            hierarchy[topic] = dict(subtopic_map)

            # Existing units are deliberately preserved without re-ingestion
            # or mutation of their IDs/source references.
            tagged_units.extend(topic_group)

        logger.info(
            "Extracted %d concepts from %d units for course %s",
            len(nodes),
            len(tagged_units),
            course_id,
        )

        return tagged_units, nodes, hierarchy
