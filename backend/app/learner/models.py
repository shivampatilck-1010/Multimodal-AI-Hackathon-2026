"""Data models for Member 4 Learner Model & Personalization Engine.

Fulfills Track D Requirement 4:
- Maintain per-topic mastery estimates updating after every quiz and conversation
  (using Bayesian Knowledge Tracing / IRT).
- Handle new students with no history (diagnostic intake).
- Adaptive recommendations using the Prerequisite DAG.
- Track student longitudinal progress and system evaluation simulations (Track D 5.c).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


MasteryStatus = Literal["needs_help", "developing", "mastered"]
RecommendationAction = Literal["review_prerequisite", "practice_quiz", "ask_tutor"]
RecommendationPriority = Literal["high", "medium", "low"]


class BKTParameters(BaseModel):
    """Bayesian Knowledge Tracing standard hyperparameters."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    p_l0: float = Field(default=0.20, description="Prior probability of knowing concept initially")
    p_transit: float = Field(default=0.15, description="Probability of learning concept on each step")
    p_guess: float = Field(default=0.25, description="Probability of guessing correctly without mastery")
    p_slip: float = Field(default=0.10, description="Probability of slipping (error) despite mastery")


class ConceptMastery(BaseModel):
    """Student mastery state for a single concept."""

    model_config = ConfigDict(extra="ignore")

    concept_id: str
    concept_name: str
    topic: str
    p_know: float = Field(default=0.20, ge=0.0, le=1.0, description="Bayesian probability of knowledge")
    attempts: int = 0
    correct_count: int = 0
    tutor_queries_count: int = 0
    last_interaction: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: MasteryStatus = "needs_help"

    def recalculate_status(self) -> None:
        if self.p_know >= 0.75:
            self.status = "mastered"
        elif self.p_know >= 0.45:
            self.status = "developing"
        else:
            self.status = "needs_help"


class TopicMastery(BaseModel):
    """Aggregated mastery across a curriculum topic."""

    model_config = ConfigDict(extra="ignore")

    topic_name: str
    mastery_percentage: float = 0.0
    total_concepts: int = 0
    mastered_concepts: int = 0
    status: MasteryStatus = "needs_help"


class AdaptiveRecommendation(BaseModel):
    """Targeted learning recommendation derived from mastery + prerequisite DAG."""

    model_config = ConfigDict(extra="ignore")

    concept_id: str
    concept_name: str
    topic: str
    priority: RecommendationPriority = "medium"
    reason: str
    action: RecommendationAction = "practice_quiz"
    prerequisite_blocker_id: str | None = None
    prerequisite_blocker_name: str | None = None


class LearnerProfile(BaseModel):
    """Complete student longitudinal state and personalization context."""

    model_config = ConfigDict(extra="ignore")

    user_id: str
    course_id: str
    overall_mastery: float = Field(default=0.0, ge=0.0, le=100.0)
    topics: dict[str, TopicMastery] = Field(default_factory=dict)
    concepts: dict[str, ConceptMastery] = Field(default_factory=dict)
    weak_concepts: list[str] = Field(default_factory=list)
    strong_concepts: list[str] = Field(default_factory=list)
    streak_days: int = 1
    study_time_minutes: int = 45
    questions_answered: int = 0
    tutor_turns: int = 0
    recent_activity: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[AdaptiveRecommendation] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SimulationResult(BaseModel):
    """Evaluation benchmark output simulating multiple student trajectories (Track D 5.c)."""

    model_config = ConfigDict(extra="ignore")

    num_students: int
    num_sessions: int
    average_initial_mastery: float
    average_final_mastery: float
    mastery_gain_percentage: float
    question_repetition_rate: float
    sessions_history: list[dict[str, Any]]
