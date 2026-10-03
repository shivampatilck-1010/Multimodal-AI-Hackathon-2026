"""Core data models for the source-grounded tutor.

These models are the integration contract between:
  * Member 1 (ingestion)   -> produces ``ContentUnit`` objects
  * Member 2 (tutor, here) -> produces ``Citation`` / ``TutorAnswer`` objects
  * Member 3 (assessment)  -> consumes ``RetrievedChunk`` and ``Citation``
  * Member 4 (learner)     -> consumes ``TutorTurnEvent`` and ``DebugTrace``

Every citation shown to a student is built from a ``SourceReference`` that came
from the knowledge base, never from free-form LLM output.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

# ---------------------------------------------------------------------------
# Identifiers
# ---------------------------------------------------------------------------

ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:\-]{0,199}$"
CourseId = Annotated[str, Field(pattern=ID_PATTERN, description="Course identifier")]
ChunkId = Annotated[str, Field(pattern=ID_PATTERN, description="Content unit identifier")]

_TIMESTAMP_RE = re.compile(r"^(?:(\d{1,2}):)?([0-5]?\d):([0-5]\d)(?:\.\d+)?$")


def parse_timestamp(value: str) -> int:
    """Convert ``HH:MM:SS`` / ``MM:SS`` (optionally with fractional seconds) to seconds."""
    match = _TIMESTAMP_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid timestamp {value!r}; expected HH:MM:SS or MM:SS")
    hours, minutes, seconds = match.groups()
    return int(hours or 0) * 3600 + int(minutes) * 60 + int(seconds)


def format_timestamp(total_seconds: int) -> str:
    hours, rem = divmod(int(total_seconds), 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


# ---------------------------------------------------------------------------
# Source references (provenance)
# ---------------------------------------------------------------------------


class _SourceBase(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    file_name: str = Field(min_length=1, max_length=300)
    # Optional stable document id assigned by ingestion (Member 1). Used for
    # source-viewer links; falls back to file_name when absent.
    file_id: str | None = Field(default=None, max_length=200)

    @property
    def document_key(self) -> str:
        return self.file_id or self.file_name


class PdfSource(_SourceBase):
    type: Literal["pdf"] = "pdf"
    page: int = Field(ge=1)

    def location_label(self) -> str:
        return f"Page {self.page}"

    def link_query(self) -> dict[str, str]:
        return {"page": str(self.page)}


class SlideSource(_SourceBase):
    type: Literal["slide"] = "slide"
    slide: int = Field(ge=1)

    def location_label(self) -> str:
        return f"Slide {self.slide}"

    def link_query(self) -> dict[str, str]:
        return {"slide": str(self.slide)}


class VideoSource(_SourceBase):
    type: Literal["video"] = "video"
    timestamp_start: str
    timestamp_end: str | None = None

    @field_validator("timestamp_start", "timestamp_end")
    @classmethod
    def _normalise_timestamp(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return format_timestamp(parse_timestamp(value))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def start_seconds(self) -> int:
        return parse_timestamp(self.timestamp_start)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def end_seconds(self) -> int | None:
        return parse_timestamp(self.timestamp_end) if self.timestamp_end else None

    def location_label(self) -> str:
        if self.timestamp_end:
            return f"{self.timestamp_start} - {self.timestamp_end}"
        return self.timestamp_start

    def link_query(self) -> dict[str, str]:
        return {"t": str(self.start_seconds)}


SourceReference = Annotated[PdfSource | SlideSource | VideoSource, Field(discriminator="type")]
SourceType = Literal["pdf", "slide", "video"]


# ---------------------------------------------------------------------------
# Knowledge-base content (Member 1 contract)
# ---------------------------------------------------------------------------


class ContentUnit(BaseModel):
    """A single retrievable unit of course material produced by ingestion."""

    model_config = ConfigDict(extra="ignore")

    id: ChunkId
    course_id: CourseId
    text: str = Field(min_length=1, max_length=20_000)
    topic: str | None = Field(default=None, max_length=300)
    concept: str | None = Field(default=None, max_length=300)
    source: SourceReference
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalFilters(BaseModel):
    """Optional metadata filters. All provided fields must match (AND)."""

    model_config = ConfigDict(extra="forbid")

    topics: list[str] | None = None
    concepts: list[str] | None = None
    source_types: list[SourceType] | None = None
    file_names: list[str] | None = None
    chunk_ids: list[str] | None = None

    def matches(self, unit: ContentUnit) -> bool:
        def _in(value: str | None, allowed: list[str] | None) -> bool:
            if allowed is None:
                return True
            return value is not None and value.casefold() in {a.casefold() for a in allowed}

        return (
            _in(unit.topic, self.topics)
            and _in(unit.concept, self.concepts)
            and (self.source_types is None or unit.source.type in self.source_types)
            and _in(unit.source.file_name, self.file_names)
            and (self.chunk_ids is None or unit.id in self.chunk_ids)
        )


class RetrievedChunk(BaseModel):
    """A content unit returned by the retriever, with its similarity score."""

    chunk_id: str
    course_id: str
    text: str
    score: float
    topic: str | None = None
    concept: str | None = None
    source: SourceReference

    @classmethod
    def from_unit(cls, unit: ContentUnit, score: float) -> RetrievedChunk:
        return cls(
            chunk_id=unit.id,
            course_id=unit.course_id,
            text=unit.text,
            score=round(float(score), 4),
            topic=unit.topic,
            concept=unit.concept,
            source=unit.source,
        )


# ---------------------------------------------------------------------------
# Tutor output
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    """A verified citation. Built exclusively from retrieved chunk metadata."""

    label: str = Field(description="Marker used inline in the answer, e.g. 'S1'")
    source_id: str = Field(description="Chunk id of the cited content unit")
    course_id: str
    source_type: SourceType
    file_name: str
    file_id: str | None = None
    page: int | None = None
    slide: int | None = None
    timestamp_start: str | None = None
    timestamp_end: str | None = None
    start_seconds: int | None = None
    location: str = Field(description="Human readable location, e.g. 'Page 183'")
    link: str = Field(description="Frontend deep link to the exact source location")
    topic: str | None = None
    concept: str | None = None
    excerpt: str


class EvidenceItem(BaseModel):
    label: str
    chunk_id: str
    score: float
    topic: str | None = None
    concept: str | None = None
    text: str
    source: SourceReference
    cited: bool


ExplanationLevel = Literal["beginner", "intermediate", "advanced"]


class TutorAnswer(BaseModel):
    answer: str
    grounded: bool
    citations: list[Citation] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    unsupported_reason: str | None = None
    outside_knowledge: str | None = Field(
        default=None,
        description="Clearly separated, NOT course-backed content (only when enabled)",
    )
    related_topics: list[str] = Field(default_factory=list)


class RetrievalTraceItem(BaseModel):
    chunk_id: str
    score: float
    topic: str | None = None
    source_type: str
    location: str
    file_name: str
    passed_threshold: bool


class DebugTrace(BaseModel):
    """Development-only trace for evaluation (faithfulness, context precision...)."""

    original_query: str
    rewritten_query: str
    rewrite_applied: bool
    retrieval_query_count: int
    retrieved: list[RetrievalTraceItem]
    grounding_threshold: float
    grounding_decision: str
    grounding_reason: str
    llm_cited_labels: list[str] = Field(default_factory=list)
    rejected_labels: list[str] = Field(default_factory=list)
    redacted_mentions: list[str] = Field(default_factory=list)
    citation_ids: list[str] = Field(default_factory=list)
    final_grounded: bool
    llm_provider: str
    embedding_provider: str
    timings_ms: dict[str, float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Conversation memory
# ---------------------------------------------------------------------------


def utcnow() -> datetime:
    return datetime.now(UTC)


class ChatMessage(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=utcnow)
    grounded: bool | None = None
    citations: list[Citation] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    rewritten_query: str | None = None
    unsupported_reason: str | None = None
    outside_knowledge: str | None = None


class Conversation(BaseModel):
    id: str
    user_id: str
    course_id: str
    title: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    messages: list[ChatMessage] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Learner-model integration (Member 4 contract)
# ---------------------------------------------------------------------------


class LearnerContext(BaseModel):
    """Personalisation hints supplied by the learner model. Never used as evidence."""

    level: ExplanationLevel | None = None
    weak_concepts: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=1000)


class TutorTurnEvent(BaseModel):
    """Emitted after every tutor turn so the learner model can update mastery."""

    user_id: str
    course_id: str
    conversation_id: str | None
    message_id: str | None
    question: str
    rewritten_query: str
    grounded: bool
    topics: list[str]
    concepts: list[str]
    cited_chunk_ids: list[str]
    level: ExplanationLevel
    created_at: datetime = Field(default_factory=utcnow)
