from app.learner.models import (
    EvidenceType,
    MasteryLevel,
    MasteryUpdateRequest,
)
from app.learner.service import LearnerModelService


def test_new_learner_profile():
    service = LearnerModelService()

    profile = service.get_or_create_profile(
        learner_id="student-1",
        course_id="course-1",
    )

    assert profile.learner_id == "student-1"
    assert profile.course_id == "course-1"
    assert profile.is_new_student is True
    assert profile.mastery_by_topic == {}


def test_quiz_updates_mastery():
    service = LearnerModelService()

    request = MasteryUpdateRequest(
        learner_id="student-1",
        course_id="course-1",
        topic_id="topic-1",
        topic_name="Algebra",
        evidence_type=EvidenceType.QUIZ,
        score=1.0,
        confidence=1.0,
        correct=True,
    )

    response = service.update_mastery(request)

    assert response.mastery > 0.0
    assert response.level == MasteryLevel.DEVELOPING
    assert response.attempts == 1
    assert response.correct_attempts == 1


def test_mastery_increases_with_repeated_correct_evidence():
    service = LearnerModelService()

    for _ in range(5):
        request = MasteryUpdateRequest(
            learner_id="student-1",
            course_id="course-1",
            topic_id="topic-1",
            topic_name="Algebra",
            evidence_type=EvidenceType.QUIZ,
            score=1.0,
            confidence=1.0,
            correct=True,
        )
        service.update_mastery(request)

    profile = service.get_profile("student-1", "course-1")

    assert profile is not None
    assert profile.mastery_by_topic["topic-1"].mastery > 0.5


def test_reset_clears_learner_state():
    service = LearnerModelService()

    service.get_or_create_profile(
        learner_id="student-1",
        course_id="course-1",
    )

    service.reset()

    profile = service.get_profile("student-1", "course-1")

    assert profile is None
