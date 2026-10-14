"""Assessment evaluation and feedback engine.

Grades student answers, flags misconceptions, validates source citations,
and generates post-assessment diagnostics reports.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.assessment.models import (
    AssessmentQuiz,
    AssessmentReport,
    QuestionEvaluation,
    StudentAnswerSubmission,
    SubmitAssessmentRequest,
)

logger = logging.getLogger(__name__)


class AssessmentEvaluator:
    """Evaluates student assessment submissions."""

    def evaluate(
        self,
        quiz: AssessmentQuiz,
        submission: SubmitAssessmentRequest,
    ) -> AssessmentReport:
        """Grade submission, identify misconceptions, and build diagnostic report."""
        evaluations: list[QuestionEvaluation] = []
        topic_scores: dict[str, list[bool]] = {}
        all_misconceptions: list[str] = []

        # Map questions by ID
        questions_by_id = {q.id: q for q in quiz.questions}

        for ans in submission.answers:
            q = questions_by_id.get(ans.question_id)
            if not q:
                continue

            user_ans = ans.selected_answer.strip()
            correct_ans = q.correct_answer.strip()

            is_correct = user_ans.casefold() == correct_ans.casefold()
            score = 1.0 if is_correct else 0.0

            # Misconception analysis
            misconception = None
            if not is_correct:
                if user_ans.upper() in q.misconception_distractors:
                    misconception = q.misconception_distractors[user_ans.upper()]
                else:
                    misconception = f"Incomplete understanding of {q.concept_name} fundamentals"
                all_misconceptions.append(f"{q.concept_name}: {misconception}")

            # Feedback with citation
            feedback = (
                f"Correct! {q.explanation}"
                if is_correct
                else f"Incorrect. The correct answer was {correct_ans}. {q.explanation} Reference: {q.source.file_name} ({q.source.location_label()})."
            )

            evaluation = QuestionEvaluation(
                question_id=q.id,
                concept_id=q.concept_id,
                concept_name=q.concept_name,
                topic=q.topic,
                question_text=q.question_text,
                is_correct=is_correct,
                score=score,
                user_answer=user_ans,
                correct_answer=correct_ans,
                feedback=feedback,
                explanation=q.explanation,
                misconception=misconception,
                source=q.source,
                chunk_id=q.chunk_id,
            )
            evaluations.append(evaluation)

            topic_scores.setdefault(q.topic, []).append(is_correct)

        total_questions = len(evaluations)
        correct_count = sum(1 for e in evaluations if e.is_correct)
        percentage = round((correct_count / total_questions * 100), 1) if total_questions > 0 else 0.0

        # Determine weak and strong topics
        weak_topics: list[str] = []
        strong_topics: list[str] = []
        for topic, results in topic_scores.items():
            acc = sum(results) / len(results)
            if acc < 0.6:
                weak_topics.append(topic)
            elif acc >= 0.8:
                strong_topics.append(topic)

        # Generate targeted recommendations
        recommendations: list[str] = []
        if weak_topics:
            for wt in weak_topics:
                recommendations.append(
                    f"Review prerequisite concepts and slides for '{wt}' before attempting advanced problems."
                )
        if all_misconceptions:
            recommendations.append(
                f"Ask the AI Tutor to clarify key distinctions: '{all_misconceptions[0]}'."
            )
        if not recommendations:
            recommendations.append("Excellent mastery! Ready to advance to the next curriculum unit.")

        return AssessmentReport(
            assessment_id=quiz.id,
            user_id=submission.user_id,
            course_id=submission.course_id,
            title=quiz.title,
            total_questions=total_questions,
            correct_count=correct_count,
            score_percentage=percentage,
            evaluations=evaluations,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            misconceptions=all_misconceptions,
            recommendations=recommendations,
            submitted_at=datetime.now(UTC),
        )
