"""Tests for Member 3 Assessment Engine."""

import pytest
from app.assessment.models import (
    GenerateAssessmentRequest,
    StudentAnswerSubmission,
    SubmitAssessmentRequest,
)
from app.assessment.service import AssessmentService
from app.tutor.knowledge_base import KnowledgeBase
from app.tutor.models import ContentUnit, PdfSource
from app.tutor.providers.embeddings import HashingEmbeddingProvider
from app.tutor.providers.llm import ExtractiveMockLLM
from app.tutor.vector_store import InMemoryVectorStore


@pytest.fixture
def assessment_setup():
    store = InMemoryVectorStore()
    embedder = HashingEmbeddingProvider()
    kb = KnowledgeBase(store=store, embedder=embedder)

    # Seed sample units
    units = [
        ContentUnit(
            id="unit_1",
            course_id="test_course",
            text="Gradient descent updates model parameters using the learning rate multiplied by the gradient of the loss.",
            topic="Optimization",
            subtopic="Gradient Descent",
            concept="Learning Rate",
            source=PdfSource(file_name="lecture1.pdf", page=12),
        ),
        ContentUnit(
            id="unit_2",
            course_id="test_course",
            text="Backpropagation calculates the gradients of the error with respect to each weight using the chain rule.",
            topic="Neural Networks",
            subtopic="Backprop",
            concept="Chain Rule",
            source=PdfSource(file_name="lecture2.pdf", page=5),
        ),
    ]
    kb.add_units(units)
    llm = ExtractiveMockLLM()
    service = AssessmentService(kb=kb, llm=llm)
    return service, kb


def test_generate_assessment(assessment_setup):
    service, _ = assessment_setup
    req = GenerateAssessmentRequest(
        course_id="test_course",
        num_questions=2,
        difficulty="medium",
    )
    quiz = service.generate_assessment(req)

    assert quiz is not None
    assert quiz.course_id == "test_course"
    assert len(quiz.questions) >= 1

    q = quiz.questions[0]
    assert q.question_text
    assert len(q.options) == 4
    assert q.correct_answer in ["A", "B", "C", "D"]
    assert q.source is not None
    assert q.chunk_id in ["unit_1", "unit_2"]


def test_submit_assessment_grading_and_feedback(assessment_setup):
    service, _ = assessment_setup
    req = GenerateAssessmentRequest(course_id="test_course", num_questions=2)
    quiz = service.generate_assessment(req)

    # Submit 1 correct and 1 incorrect answer
    q1 = quiz.questions[0]
    answers = [
        StudentAnswerSubmission(question_id=q1.id, selected_answer=q1.correct_answer),
    ]
    if len(quiz.questions) > 1:
        q2 = quiz.questions[1]
        wrong_choice = "B" if q2.correct_answer != "B" else "C"
        answers.append(StudentAnswerSubmission(question_id=q2.id, selected_answer=wrong_choice))

    sub = SubmitAssessmentRequest(
        assessment_id=quiz.id,
        user_id="student_test",
        course_id="test_course",
        answers=answers,
    )
    report = service.submit_assessment(sub)

    assert report.total_questions == len(answers)
    assert report.correct_count >= 1
    assert len(report.evaluations) == len(answers)

    first_eval = report.evaluations[0]
    assert first_eval.is_correct is True
    assert first_eval.score == 1.0
    assert "lecture" in first_eval.source.file_name

    # Check that report is stored in history
    history = service.get_user_reports("student_test")
    assert len(history) == 1
    assert history[0].assessment_id == quiz.id
