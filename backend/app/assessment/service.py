"""Assessment Service orchestrator."""

from __future__ import annotations

import logging
from typing import Any

from app.assessment.evaluator import AssessmentEvaluator
from app.assessment.generator import AssessmentGenerator
from app.assessment.models import (
    AssessmentQuiz,
    AssessmentReport,
    GenerateAssessmentRequest,
    SubmitAssessmentRequest,
)
from app.kb.graph_store import GraphStore
from app.kb.media_store import MediaStore
from app.tutor.knowledge_base import KnowledgeBase
from app.tutor.providers.llm import LLMProvider

logger = logging.getLogger(__name__)


class AssessmentService:
    """Service managing quiz generation, grading, and telemetry dispatches."""

    def __init__(
        self,
        kb: KnowledgeBase,
        llm: LLMProvider,
        graph_store: GraphStore | None = None,
        media_store: MediaStore | None = None,
    ) -> None:
        self.generator = AssessmentGenerator(kb, llm, graph_store, media_store)
        self.evaluator = AssessmentEvaluator()
        self.active_quizzes: dict[str, AssessmentQuiz] = {}
        self.reports_history: dict[str, list[AssessmentReport]] = {}
        self._learner_service: Any = None  # Set dynamically to avoid circular imports

    def set_learner_service(self, learner_service: Any) -> None:
        """Register Member 4 Learner Model service to receive assessment telemetry."""
        self._learner_service = learner_service

    def generate_assessment(self, req: GenerateAssessmentRequest) -> AssessmentQuiz:
        """Generate and store an assessment quiz."""
        quiz = self.generator.generate_quiz(req)
        self.active_quizzes[quiz.id] = quiz
        logger.info(f"Generated quiz '{quiz.id}' with {len(quiz.questions)} questions for {req.course_id}")
        return quiz

    def get_assessment(self, quiz_id: str) -> AssessmentQuiz | None:
        return self.active_quizzes.get(quiz_id)

    def submit_assessment(self, submission: SubmitAssessmentRequest) -> AssessmentReport:
        """Grade quiz, store diagnostic report, and notify Learner Model."""
        quiz = self.active_quizzes.get(submission.assessment_id)
        if not quiz:
            raise KeyError(f"Assessment quiz {submission.assessment_id} not found or expired")

        report = self.evaluator.evaluate(quiz, submission)

        # Store in user history
        self.reports_history.setdefault(submission.user_id, []).append(report)

        # Dispatch telemetry to Member 4 Learner Model
        if self._learner_service is not None:
            try:
                self._learner_service.on_assessment_completed(report)
                logger.info(
                    f"Dispatched assessment report '{report.assessment_id}' to Learner Model for user '{submission.user_id}'"
                )
            except Exception as e:
                logger.error(f"Failed to dispatch assessment telemetry to Learner Model: {e}")

        return report

    def get_user_reports(self, user_id: str) -> list[AssessmentReport]:
        return self.reports_history.get(user_id, [])
