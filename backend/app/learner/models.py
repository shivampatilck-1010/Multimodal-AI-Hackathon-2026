from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceType(str, Enum):
    QUIZ = "quiz"
    CONVERSATION = "conversation"
    DIAGNOSTIC = "diagnostic"


class MasteryLevel(str, Enum):
    NOVICE = "novice"
    DEVELOPING = "developing"
    PROFICIENT = "proficient"
    MASTERED = "mastered"


class MasteryEvidence(BaseModel):
    """
    A single learning signal used to update a student's mastery estimate.
    """

    model_config = ConfigDict(extra="forbid")

    evidence_type: EvidenceType
    score: float = Field(ge=0.0, le=1.0)
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    source_id: str | None = Field(default=None, min_length=1)
    question_id: str | None = Field(default=None, min_length=1)

    correct: bool | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    misconception: str | None = Field(default=None, min_length=1)


class TopicMastery(BaseModel):
    """
    Current mastery state for one topic.

    mastery is deliberately represented as a normalized probability-like
    estimate in [0, 1]. The update algorithm is implemented separately.
    """

    model_config = ConfigDict(extra="forbid")

    topic_id: str = Field(min_length=1)
    topic_name: str = Field(min_length=1)

    mastery: float = Field(default=0.0, ge=0.0, le=1.0)

    attempts: int = Field(default=0, ge=0)
    correct_attempts: int = Field(default=0, ge=0)

    level: MasteryLevel = MasteryLevel.NOVICE

    last_evidence_at: datetime | None = None

    recent_evidence: list[MasteryEvidence] = Field(
        default_factory=list
    )


class LearnerProfile(BaseModel):
    """
    Persistent learner state for a student within a course.

    A profile can exist before the student has completed any assessment.
    That allows the system to represent a genuinely new learner.
    """

    model_config = ConfigDict(extra="forbid")

    learner_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)

    mastery_by_topic: dict[str, TopicMastery] = Field(
        default_factory=dict
    )

    total_interactions: int = Field(default=0, ge=0)
    total_assessments: int = Field(default=0, ge=0)

    is_new_student: bool = True

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class MasteryUpdateRequest(BaseModel):
    """
    Input to the learner-model service after a learning interaction.
    """

    model_config = ConfigDict(extra="forbid")

    learner_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)

    topic_id: str = Field(min_length=1)
    topic_name: str = Field(min_length=1)

    evidence_type: EvidenceType

    score: float = Field(ge=0.0, le=1.0)

    source_id: str | None = Field(default=None, min_length=1)
    question_id: str | None = Field(default=None, min_length=1)

    correct: bool | None = None

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    misconception: str | None = Field(
        default=None,
        min_length=1,
    )


class MasteryUpdateResponse(BaseModel):
    """
    Result returned after applying one learning signal.
    """

    model_config = ConfigDict(extra="forbid")

    learner_id: str
    course_id: str

    topic_id: str
    topic_name: str

    previous_mastery: float = Field(ge=0.0, le=1.0)
    mastery: float = Field(ge=0.0, le=1.0)

    previous_level: MasteryLevel
    level: MasteryLevel

    attempts: int = Field(ge=0)
    correct_attempts: int = Field(ge=0)

    evidence_type: EvidenceType
    updated_at: datetime