"""Prerequisite relationship builder and DAG discovery."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.kb.models import ConceptNode, PrerequisiteEdge, CourseKnowledgeGraph

logger = logging.getLogger(__name__)

PREREQUISITE_PROMPT = """You are an academic curriculum designer.
Given these educational concepts in a course:
{concepts_list}

Identify prerequisite dependencies between them.
A prerequisite means: "A student MUST understand Concept A before they can understand Concept B."

Return a valid JSON object matching this structure:
{{
  "prerequisites": [
    {{
      "source_concept": "Concept A Name",
      "target_concept": "Concept B Name",
      "rationale": "Clear pedagogical explanation of why A is needed for B",
      "strength": 0.9
    }}
  ]
}}
Only return dependencies that are strictly necessary. Do NOT create circular dependencies.
Only return valid JSON, no markdown code fence.
"""


class PrerequisiteGraphBuilder:
    """Discovers prerequisite dependencies and constructs the CourseKnowledgeGraph."""

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

    def build_graph(
        self,
        course_id: str,
        nodes: dict[str, ConceptNode],
        hierarchy: dict[str, dict[str, list[str]]],
    ) -> CourseKnowledgeGraph:
        """Discover prerequisite relationships and return CourseKnowledgeGraph."""
        if not nodes:
            return CourseKnowledgeGraph(course_id=course_id, nodes={}, edges=[])

        edges: list[PrerequisiteEdge] = []

        if self._client and len(nodes) > 1:
            try:
                edges = self._discover_with_gemini(nodes)
            except Exception as e:
                logger.warning(f"gemini_prerequisite_discovery_failed: {e}")
                edges = self._discover_linear_heuristic(nodes)
        else:
            edges = self._discover_linear_heuristic(nodes)

        return CourseKnowledgeGraph(
            course_id=course_id,
            nodes=nodes,
            edges=edges,
            topics_hierarchy=hierarchy,
        )

    def _discover_linear_heuristic(
        self,
        nodes: dict[str, ConceptNode],
    ) -> list[PrerequisiteEdge]:
        """Pedagogical default: concepts appearing earlier in course materials precede later ones."""
        edges: list[PrerequisiteEdge] = []
        node_list = list(nodes.values())

        for i in range(len(node_list) - 1):
            source = node_list[i]
            target = node_list[i + 1]
            edges.append(
                PrerequisiteEdge(
                    source_concept_id=source.id,
                    target_concept_id=target.id,
                    relation_type="prerequisite_of",
                    rationale=f"Foundational concepts in '{source.topic}: {source.name}' precede '{target.topic}: {target.name}'.",
                    strength=0.8,
                )
            )

        return edges

    def _discover_with_gemini(
        self,
        nodes: dict[str, ConceptNode],
    ) -> list[PrerequisiteEdge]:
        concepts_summary = "\n".join(
            f"- {n.name} (Topic: {n.topic}): {n.summary}" for n in nodes.values()
        )
        prompt = PREREQUISITE_PROMPT.format(concepts_list=concepts_summary)
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

        name_to_id = {n.name.lower(): n.id for n in nodes.values()}
        edges: list[PrerequisiteEdge] = []

        for p in parsed.get("prerequisites", []):
            s_name = p.get("source_concept", "").strip().lower()
            t_name = p.get("target_concept", "").strip().lower()

            s_id = name_to_id.get(s_name)
            t_id = name_to_id.get(t_name)

            if s_id and t_id and s_id != t_id:
                edges.append(
                    PrerequisiteEdge(
                        source_concept_id=s_id,
                        target_concept_id=t_id,
                        relation_type="prerequisite_of",
                        rationale=p.get("rationale", "Prerequisite relationship"),
                        strength=float(p.get("strength", 1.0)),
                    )
                )

        return edges
