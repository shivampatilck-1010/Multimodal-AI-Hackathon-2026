"""Data models for Member 3 Adaptive Assessment Engine.

Fulfills Track D Requirement 3:
- Generate quizzes and mock exams (MCQ, short answer, numerical problems)
  on student-chosen scope, with each question tagged to topic, source location,
  and difficulty.
- Verify question correctness and avoid repeated questions across assessments.
- Provide cited feedback on each answer and a post-assessment report identifying
  weak topics and likely misconceptions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

from app.tutor.models import CourseId, SourceReference


QuestionType = Literal["mcq", "short_answer", "numerical"]
DifficultyLevel = Literal["easy", "medium", "hard"]


class QuestionOption(BaseModel):
    """An option choice for multiple-choice questions."""

    model_config = ConfigDict(extra="ignore")

    key: str = Field(description="Option key, e.g. 'A', 'B', 'C', 'D'")
    text: str = Field(description="Option content text")


class AssessmentQuestion(BaseModel):
    """A single source-grounded assessment question."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique question identifier, e.g. 'q_backprop_001'")
    course_id: CourseId
    concept_id: str = Field(description="Underlying concept being tested")
    concept_name: str = Field(description="Human readable concept name")
    topic: str = Field(description="Course topic name")
    subtopic: str | None = None
    question_type: QuestionType = "mcq"
    difficulty: DifficultyLevel = "medium"
    question_text: str = Field(description="The question prompt")
    options: list[QuestionOption] = Field(
        default_factory=list, description="Available choices for MCQs"
    )
    correct_answer: str = Field(description="Key (e.g. 'B') or exact expected value")
    explanation: str = Field(
        description="Source-grounded explanation for why the answer is correct"
    )
    misconception_distractors: dict[str, str] = Field(
        default_factory=dict,
        description="Map of incorrect option key -> common misconception it represents",
    )
    source: SourceReference = Field(
        description="Exact location provenance (page, slide, or video timestamp)"
    )
    chunk_id: str = Field(description="Knowledge base chunk ID backing this question")
    figure_id: str | None = Field(
        default=None, description="Optional associated diagram figure ID"
    )


class AssessmentQuiz(BaseModel):
    """A generated assessment set containing multiple questions."""

    model_config = ConfigDict(extra="ignore")

    id: str = Field(description="Unique quiz session identifier")
    course_id: CourseId
    title: str = Field(description="Quiz title")
    topic: str | None = None
    concept_id: str | None = None
    difficulty: DifficultyLevel = "medium"
    questions: list[AssessmentQuestion] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GenerateAssessmentRequest(BaseModel):
    """Request payload to generate a new adaptive assessment."""

    model_config = ConfigDict(extra="ignore")

    course_id: str = "hackathon_course"
    topic: str | None = None
    concept_id: str | None = None
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: DifficultyLevel = "medium"
    question_types: list[QuestionType] = Field(default_factory=lambda: ["mcq"])


class StudentAnswerSubmission(BaseModel):
    """A student's submitted response to a single question."""

    model_config = ConfigDict(extra="ignore")

    question_id: str
    selected_answer: str = Field(
        description="Selected option key (e.g. 'B') or written answer"
    )
    time_spent_seconds: int | None = None


class SubmitAssessmentRequest(BaseModel):
    """Submission payload for an entire assessment."""

    model_config = ConfigDict(extra="ignore")

    assessment_id: str
    user_id: str = "student_alex"
    course_id: str = "hackathon_course"
    answers: list[StudentAnswerSubmission]


class QuestionEvaluation(BaseModel):
    """Individual grading result for a question."""

    model_config = ConfigDict(extra="ignore")

    question_id: str
    concept_id: str
    concept_name: str
    topic: str
    question_text: str
    is_correct: bool
    score: float = Field(ge=0.0, le=1.0, description="Normalized score 0.0 to 1.0")
    user_answer: str
    correct_answer: str
    feedback: str
    explanation: str
    misconception: str | None = None
    source: SourceReference
    chunk_id: str


class AssessmentReport(BaseModel):
    """Comprehensive post-assessment report identifying performance & misconceptions."""

    model_config = ConfigDict(extra="ignore")

    assessment_id: str
    user_id: str
    course_id: str
    title: str
    total_questions: int
    correct_count: int
    score_percentage: float
    evaluations: list[QuestionEvaluation]
    weak_topics: list[str] = Field(
        default_factory=list, description="Topics with score < 60%"
    )
    strong_topics: list[str] = Field(
        default_factory=list, description="Topics with score >= 80%"
    )
    misconceptions: list[str] = Field(
        default_factory=list, description="Identified student misconceptions"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable pedagogical next steps"
    )
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
