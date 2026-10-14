"""Learner Model API routes for Member 4."""

from __future__ import annotations

import logging
from typing import Any, List

from fastapi import APIRouter, HTTPException, Query

from app.learner.models import AdaptiveRecommendation, LearnerProfile, SimulationResult
from app.tutor.models import TutorTurnEvent

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{user_id}/dashboard")
async def get_student_dashboard(
    user_id: str,
    course_id: str = Query(default="hackathon_course"),
):
    """Retrieve full live student dashboard payload matching frontend contract."""
    from app.main import learner_service

    if not learner_service:
        raise HTTPException(status_code=503, detail="Learner service not ready")

    try:
        return learner_service.get_dashboard_data(user_id, course_id)
    except Exception as e:
        logger.error(f"Failed to fetch dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/profile", response_model=LearnerProfile)
async def get_student_profile(
    user_id: str,
    course_id: str = Query(default="hackathon_course"),
):
    """Retrieve raw longitudinal learner profile including all concept masteries."""
    from app.main import learner_service

    if not learner_service:
        raise HTTPException(status_code=503, detail="Learner service not ready")

    return learner_service.get_or_create_profile(user_id, course_id)


@router.get("/{user_id}/recommendations", response_model=List[AdaptiveRecommendation])
async def get_student_recommendations(
    user_id: str,
    course_id: str = Query(default="hackathon_course"),
):
    """Fetch adaptive next steps with prerequisite root cause gap analysis."""
    from app.main import learner_service

    if not learner_service:
        raise HTTPException(status_code=503, detail="Learner service not ready")

    profile = learner_service.get_or_create_profile(user_id, course_id)
    return profile.recommendations


@router.post("/{user_id}/events/tutor")
async def log_tutor_event(user_id: str, event: TutorTurnEvent):
    """Receive conversational tutor telemetry to update learner mastery."""
    from app.main import learner_service

    if not learner_service:
        raise HTTPException(status_code=503, detail="Learner service not ready")

    learner_service.on_tutor_turn(event)
    return {"status": "ok"}


@router.post("/{user_id}/reset")
async def reset_student_profile(
    user_id: str,
    course_id: str = Query(default="hackathon_course"),
):
    """Reset student profile to pristine baseline (useful for live demo intake)."""
    from app.main import learner_service

    if not learner_service:
        raise HTTPException(status_code=503, detail="Learner service not ready")

    key = (user_id, course_id)
    if key in learner_service.profiles:
        del learner_service.profiles[key]

    new_profile = learner_service.get_or_create_profile(user_id, course_id)
    return {"status": "reset_successful", "profile": new_profile}


@router.get("/simulation/run", response_model=SimulationResult)
async def run_learner_simulation(
    course_id: str = Query(default="hackathon_course"),
    students: int = Query(default=5, ge=1, le=50),
    sessions: int = Query(default=6, ge=1, le=20),
):
    """Run Track D 5.c benchmark simulation across student cohorts."""
    from app.main import learner_service

    if not learner_service:
        raise HTTPException(status_code=503, detail="Learner service not ready")

    try:
        return learner_service.run_student_simulation(
            course_id=course_id,
            num_students=students,
            num_sessions=sessions,
        )
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
