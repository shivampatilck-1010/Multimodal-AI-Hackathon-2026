"""Extended models for Member 1 Knowledge Base, Figures, and Prerequisite Graph.

Maintains 100% interoperability with Member 2's ``ContentUnit`` and ``SourceReference``.
"""

from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from app.tutor.models import (
    ChunkId,
    CourseId,
    PdfSource,
    SlideSource,
    VideoSource,
    SourceReference,
    SourceType,
    ContentUnit,
)


class BoundingBox(BaseModel):
    """Bounding box coordinates on a page or slide."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    x0: float = Field(description="Left coordinate")
    y0: float = Field(description="Top coordinate")
    x1: float = Field(description="Right coordinate")
    y1: float = Field(description="Bottom coordinate")
    width: float | None = None
    height: float | None = None


class FigureUnit(BaseModel):
    """An extracted diagram, figure, chart, or image with full provenance."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique identifier for the figure, e.g. fig_bio101_p42_1")
    course_id: CourseId
    source: SourceReference
    image_rel_path: str = Field(description="Relative path to stored image file")
    caption: str = Field(default="", description="Extracted or generated figure caption")
    explanation: str = Field(
        default="", description="Detailed multimodal explanation of the visual diagram"
    )
    associated_concepts: list[str] = Field(
        default_factory=list, description="Concepts linked to this figure"
    )
    bounding_box: BoundingBox | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConceptNode(BaseModel):
    """A single conceptual knowledge unit within a course curriculum."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique concept ID, e.g. concept_photosynthesis_calvin_cycle")
    course_id: CourseId
    name: str = Field(description="Human readable concept name, e.g. 'Calvin Cycle'")
    topic: str = Field(description="Major topic name, e.g. 'Photosynthesis'")
    subtopic: str | None = Field(default=None, description="Subtopic name, e.g. 'Light-Independent Reactions'")
    summary: str = Field(default="", description="Definitive 1-2 sentence concept definition")
    content_unit_ids: list[str] = Field(
        default_factory=list, description="IDs of ContentUnits covering this concept"
    )
    figure_ids: list[str] = Field(
        default_factory=list, description="IDs of FigureUnits illustrating this concept"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class PrerequisiteEdge(BaseModel):
    """Directed relationship where source_concept_id must be understood before target_concept_id."""

    model_config = ConfigDict(extra="ignore")

    source_concept_id: str = Field(
        description="Prerequisite concept ID (must learn first)"
    )
    target_concept_id: str = Field(
        description="Dependent concept ID (requires prerequisite)"
    )
    relation_type: Literal["prerequisite_of", "related_to"] = "prerequisite_of"
    rationale: str = Field(
        default="", description="Pedagogical explanation of why this prerequisite is required"
    )
    strength: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence or strictness of the dependency"
    )


class CourseKnowledgeGraph(BaseModel):
    """Complete course graph containing concept nodes, prerequisite edges, and hierarchy."""

    model_config = ConfigDict(extra="ignore")

    course_id: CourseId
    nodes: dict[str, ConceptNode] = Field(
        default_factory=dict, description="Lookup of concept_id -> ConceptNode"
    )
    edges: list[PrerequisiteEdge] = Field(
        default_factory=list, description="List of prerequisite dependencies"
    )
    topics_hierarchy: dict[str, dict[str, list[str]]] = Field(
        default_factory=dict,
        description="Hierarchical map: Topic -> Subtopic -> list of Concept IDs",
    )

    def get_prerequisites(self, concept_id: str) -> list[str]:
        """Return list of concept IDs that are prerequisites for concept_id."""
        return [
            e.source_concept_id
            for e in self.edges
            if e.target_concept_id == concept_id and e.relation_type == "prerequisite_of"
        ]

    def get_dependents(self, concept_id: str) -> list[str]:
        """Return list of concept IDs that depend on concept_id."""
        return [
            e.target_concept_id
            for e in self.edges
            if e.source_concept_id == concept_id and e.relation_type == "prerequisite_of"
        ]


class IngestSummary(BaseModel):
    """Summary returned after processing course files."""

    course_id: str
    files_processed: list[str] = Field(default_factory=list)
    units_count: int = 0
    figures_count: int = 0
    concepts_count: int = 0
    prerequisites_count: int = 0
    errors: list[str] = Field(default_factory=list)
