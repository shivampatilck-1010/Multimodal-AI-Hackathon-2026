"""Concept and taxonomy extractor for topics, subtopics, and key concepts."""

from __future__ import annotations

import json
import logging
import re
from collections import Counter
from typing import Any

from app.tutor.models import ContentUnit
from app.kb.models import ConceptNode, FigureUnit

logger = logging.getLogger(__name__)

TAXONOMY_PROMPT = """You are an academic curriculum designer.
Analyze the following course material excerpts from course: {course_id}.

Extract a coherent pedagogical curriculum taxonomy:
1. Major Topics (e.g. "Photosynthesis", "Cellular Respiration")
2. Subtopics under each topic (e.g. "Light Reactions", "Calvin Cycle")
3. Key Concepts under each subtopic (e.g. "Thylakoid Membrane", "ATP Synthase")

Course excerpts:
{excerpts}

Return a valid JSON object matching this structure:
{{
  "topics": [
    {{
      "name": "Topic Name",
      "subtopics": [
        {{
          "name": "Subtopic Name",
          "concepts": [
            {{
              "name": "Concept Name",
              "summary": "1-2 sentence core pedagogical explanation"
            }}
          ]
        }}
      ]
    }}
  ]
}}
Only return the valid JSON, no markdown code fence.
"""


class ConceptExtractor:
    """Discovers topics, subtopics, and key concepts and tags ContentUnits."""

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
            except Exception as e:
                logger.warning(f"could_not_initialize_genai_client: {e}")

    def extract_taxonomy(
        self,
        course_id: str,
        units: list[ContentUnit],
        figures: list[FigureUnit] | None = None,
    ) -> tuple[list[ContentUnit], dict[str, ConceptNode], dict[str, dict[str, list[str]]]]:
        """Identify topics, subtopics, concepts, tag units, and build ConceptNodes."""
        if not units:
            return [], {}, {}

        # 1. Check if Gemini is available for LLM-based taxonomy discovery
        nodes: dict[str, ConceptNode] = {}
        hierarchy: dict[str, dict[str, list[str]]] = {}

        if self._client:
            try:
                nodes, hierarchy = self._extract_with_gemini(course_id, units)
            except Exception as e:
                logger.warning(f"gemini_taxonomy_extraction_failed: {e}")
                nodes, hierarchy = self._extract_heuristic(course_id, units)
        else:
            nodes, hierarchy = self._extract_heuristic(course_id, units)

        # 2. Tag units with matching concepts
        tagged_units = self._tag_units(units, nodes)

        # 3. Associate figures with concepts
        if figures:
            self._link_figures(nodes, figures)

        return tagged_units, nodes, hierarchy

    def _extract_heuristic(
        self,
        course_id: str,
        units: list[ContentUnit],
    ) -> tuple[dict[str, ConceptNode], dict[str, dict[str, list[str]]]]:
        """Heuristic offline taxonomy extraction based on headers, titles, and frequency."""
        nodes: dict[str, ConceptNode] = {}
        hierarchy: dict[str, dict[str, list[str]]] = {}

        # Collect candidate titles from slides and headings
        candidates: list[str] = []
        for u in units:
            # Check metadata title
            if u.metadata.get("title"):
                candidates.append(u.metadata["title"].strip())
            # Check markdown headers: # Header or ## Header
            for line in u.text.splitlines():
                line = line.strip()
                if line.startswith("#"):
                    header = re.sub(r"^#+\s*", "", line).strip()
                    if len(header) >= 3 and len(header) <= 60:
                        candidates.append(header)

        # Count frequencies
        counts = Counter(candidates)
        top_terms = [term for term, _ in counts.most_common(12)]
        if not top_terms:
            top_terms = ["General Concepts", "Core Material"]

        # Formulate fallback hierarchy
        main_topic = top_terms[0] if top_terms else "Course Overview"
        hierarchy[main_topic] = {"Key Concepts": []}

        for i, term in enumerate(top_terms):
            cid = f"concept_{re.sub(r'[^A-Za-z0-9_]+', '_', term.lower())}"
            hierarchy[main_topic]["Key Concepts"].append(cid)
            nodes[cid] = ConceptNode(
                id=cid,
                course_id=course_id,
                name=term,
                topic=main_topic,
                subtopic="Key Concepts",
                summary=f"Foundational understanding of {term}.",
                content_unit_ids=[],
                figure_ids=[],
            )

        return nodes, hierarchy

    def _extract_with_gemini(
        self,
        course_id: str,
        units: list[ContentUnit],
    ) -> tuple[dict[str, ConceptNode], dict[str, dict[str, list[str]]]]:
        # Take representative excerpts across chunks
        sample_units = units[:25]
        excerpts = "\n\n".join(
            f"--- Unit {u.id} ({u.source.location_label()}) ---\n{u.text[:400]}"
            for u in sample_units
        )
        prompt = TAXONOMY_PROMPT.format(course_id=course_id, excerpts=excerpts)
        response = self._client.models.generate_content(
            model=self.model,
            contents=[prompt],
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        parsed = json.loads(text.strip())

        nodes: dict[str, ConceptNode] = {}
        hierarchy: dict[str, dict[str, list[str]]] = {}

        for t in parsed.get("topics", []):
            topic_name = t.get("name", "General")
            hierarchy.setdefault(topic_name, {})
            for sub in t.get("subtopics", []):
                sub_name = sub.get("name", "Core")
                hierarchy[topic_name].setdefault(sub_name, [])
                for c in sub.get("concepts", []):
                    c_name = c.get("name", "")
                    if not c_name:
                        continue
                    cid = f"concept_{re.sub(r'[^A-Za-z0-9_]+', '_', c_name.lower())}"
                    hierarchy[topic_name][sub_name].append(cid)
                    nodes[cid] = ConceptNode(
                        id=cid,
                        course_id=course_id,
                        name=c_name,
                        topic=topic_name,
                        subtopic=sub_name,
                        summary=c.get("summary", ""),
                        content_unit_ids=[],
                        figure_ids=[],
                    )

        return nodes, hierarchy

    def _tag_units(
        self,
        units: list[ContentUnit],
        nodes: dict[str, ConceptNode],
    ) -> list[ContentUnit]:
        """Tag each ContentUnit with best matching topic and concept."""
        for u in units:
            unit_text_lower = u.text.lower()
            matched_concept: ConceptNode | None = None

            for node in nodes.values():
                # Case-insensitive term boundary check
                if re.search(r"\b" + re.escape(node.name.lower()) + r"\b", unit_text_lower):
                    matched_concept = node
                    break

            if matched_concept:
                u.topic = matched_concept.topic
                u.concept = matched_concept.name
                matched_concept.content_unit_ids.append(u.id)
            elif not u.topic and nodes:
                # Default to first topic
                first_node = next(iter(nodes.values()))
                u.topic = first_node.topic
                u.concept = first_node.name
                first_node.content_unit_ids.append(u.id)

        return units

    def _link_figures(
        self,
        nodes: dict[str, ConceptNode],
        figures: list[FigureUnit],
    ) -> None:
        """Associate figures with matching concepts."""
        for fig in figures:
            for node in nodes.values():
                for c in fig.associated_concepts:
                    if c.strip().lower() == node.name.lower():
                        if fig.id not in node.figure_ids:
                            node.figure_ids.append(fig.id)
