from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.learner.models import (
    LearnerProfile,
    MasteryUpdateRequest,
    MasteryUpdateResponse,
)
from app.learner.service import LearnerModelService


router = APIRouter(
    prefix="/learners",
    tags=["Learner Model"],
)

learner_service = LearnerModelService()


@router.get(
    "/{learner_id}/courses/{course_id}/profile",
    response_model=LearnerProfile,
)
def get_learner_profile(
    learner_id: str,
    course_id: str,
) -> LearnerProfile:
    """
    Return the learner's mastery profile for a course.

    A new learner receives an initialized profile with no topic history.
    """
    profile = learner_service.get_or_create_profile(
        learner_id=learner_id,
        course_id=course_id,
    )

    return profile


@router.post(
    "/mastery",
    response_model=MasteryUpdateResponse,
    status_code=status.HTTP_200_OK,
)
def update_learner_mastery(
    request: MasteryUpdateRequest,
) -> MasteryUpdateResponse:
    """
    Update topic mastery from quiz, conversation, or diagnostic evidence.
    """
    try:
        return learner_service.update_mastery(request)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported evidence type: {exc.args[0]}",
        ) from exc


@router.post(
    "/reset",
    status_code=status.HTTP_204_NO_CONTENT,
)
def reset_learner_state() -> None:
    """
    Clear all in-memory learner state.

    Intended for local development and deterministic testing.
    """
    learner_service.reset()