from __future__ import annotations

from datetime import datetime, timezone

from .models import (
    EvidenceType,
    LearnerProfile,
    MasteryEvidence,
    MasteryLevel,
    MasteryUpdateRequest,
    MasteryUpdateResponse,
    TopicMastery,
)


class LearnerModelService:
    """
    Stateful in-memory learner model.

    Persistence will be added separately. Keeping the state-management
    boundary here allows the API layer and future persistence layer to
    remain independent of the mastery algorithm.
    """

    MAX_RECENT_EVIDENCE = 20

    # Initial learner mastery. A student with no evidence is intentionally
    # treated as a novice rather than being assumed proficient.
    INITIAL_MASTERY = 0.0

    # Evidence learning rates. Stronger evidence moves mastery more.
    LEARNING_RATES = {
        EvidenceType.QUIZ: 0.35,
        EvidenceType.CONVERSATION: 0.20,
        EvidenceType.DIAGNOSTIC: 0.45,
    }

    def __init__(self) -> None:
        self._profiles: dict[tuple[str, str], LearnerProfile] = {}

    def get_or_create_profile(
        self,
        learner_id: str,
        course_id: str,
    ) -> LearnerProfile:
        key = (learner_id, course_id)

        profile = self._profiles.get(key)
        if profile is not None:
            return profile

        now = datetime.now(timezone.utc)

        profile = LearnerProfile(
            learner_id=learner_id,
            course_id=course_id,
            mastery_by_topic={},
            total_interactions=0,
            total_assessments=0,
            is_new_student=True,
            created_at=now,
            updated_at=now,
        )

        self._profiles[key] = profile
        return profile

    def get_profile(
        self,
        learner_id: str,
        course_id: str,
    ) -> LearnerProfile | None:
        return self._profiles.get((learner_id, course_id))

    def update_mastery(
        self,
        request: MasteryUpdateRequest,
    ) -> MasteryUpdateResponse:
        profile = self.get_or_create_profile(
            learner_id=request.learner_id,
            course_id=request.course_id,
        )

        topic = profile.mastery_by_topic.get(request.topic_id)

        if topic is None:
            topic = TopicMastery(
                topic_id=request.topic_id,
                topic_name=request.topic_name,
                mastery=self.INITIAL_MASTERY,
                attempts=0,
                correct_attempts=0,
                level=MasteryLevel.NOVICE,
            )
            profile.mastery_by_topic[request.topic_id] = topic

        previous_mastery = topic.mastery
        previous_level = topic.level

        learning_rate = self.LEARNING_RATES[request.evidence_type]

        # Confidence scales the strength of the learning signal.
        effective_rate = learning_rate * request.confidence

        # The target represents the observed learning outcome:
        # 1.0 = strong evidence of mastery
        # 0.0 = evidence of non-mastery.
        target = request.score

        new_mastery = previous_mastery + (
            effective_rate * (target - previous_mastery)
        )

        # Defensive numerical bounds.
        new_mastery = max(0.0, min(1.0, new_mastery))

        topic.mastery = new_mastery

        if request.evidence_type in {
            EvidenceType.QUIZ,
            EvidenceType.DIAGNOSTIC,
        }:
            topic.attempts += 1

            if request.correct is True:
                topic.correct_attempts += 1

            profile.total_assessments += 1
        else:
            profile.total_interactions += 1

        topic.level = self._classify_mastery(new_mastery)
        topic.last_evidence_at = datetime.now(timezone.utc)

        evidence = MasteryEvidence(
            evidence_type=request.evidence_type,
            score=request.score,
            occurred_at=topic.last_evidence_at,
            source_id=request.source_id,
            question_id=request.question_id,
            correct=request.correct,
            confidence=request.confidence,
            misconception=request.misconception,
        )

        topic.recent_evidence.append(evidence)

        if len(topic.recent_evidence) > self.MAX_RECENT_EVIDENCE:
            topic.recent_evidence = topic.recent_evidence[
                -self.MAX_RECENT_EVIDENCE:
            ]

        profile.is_new_student = False
        profile.updated_at = topic.last_evidence_at

        return MasteryUpdateResponse(
            learner_id=profile.learner_id,
            course_id=profile.course_id,
            topic_id=topic.topic_id,
            topic_name=topic.topic_name,
            previous_mastery=previous_mastery,
            mastery=topic.mastery,
            previous_level=previous_level,
            level=topic.level,
            attempts=topic.attempts,
            correct_attempts=topic.correct_attempts,
            evidence_type=request.evidence_type,
            updated_at=topic.last_evidence_at,
        )

    @staticmethod
    def _classify_mastery(mastery: float) -> MasteryLevel:
        if mastery < 0.25:
            return MasteryLevel.NOVICE

        if mastery < 0.50:
            return MasteryLevel.DEVELOPING

        if mastery < 0.80:
            return MasteryLevel.PROFICIENT

        return MasteryLevel.MASTERED

    def reset(self) -> None:
        """
        Clear in-memory learner state.

        Primarily useful for deterministic tests and local development.
        """
        self._profiles.clear()