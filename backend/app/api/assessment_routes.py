"""Assessment API routes for Member 3."""

from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, HTTPException

from app.assessment.models import (
    AssessmentQuiz,
    AssessmentReport,
    GenerateAssessmentRequest,
    SubmitAssessmentRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/generate", response_model=AssessmentQuiz)
def generate_assessment(request: GenerateAssessmentRequest):
    """Generate a source-grounded quiz tailored to student scope, topic, and difficulty."""
    from app.main import assessment_service

    if not assessment_service:
        raise HTTPException(status_code=503, detail="Assessment service not ready")

    try:
        quiz = assessment_service.generate_assessment(request)
        return quiz
    except Exception as e:
        logger.exception("Failed to generate assessment")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}", response_model=AssessmentQuiz)
def get_assessment(quiz_id: str):
    """Fetch an active assessment quiz by ID."""
    from app.main import assessment_service

    if not assessment_service:
        raise HTTPException(status_code=503, detail="Assessment service not ready")

    quiz = assessment_service.get_assessment(quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return quiz


@router.post("/submit", response_model=AssessmentReport)
def submit_assessment(submission: SubmitAssessmentRequest):
    """Submit student answers, receive instant cited feedback, and trigger BKT mastery updates."""
    from app.main import assessment_service

    if not assessment_service:
        raise HTTPException(status_code=503, detail="Assessment service not ready")

    try:
        report = assessment_service.submit_assessment(submission)
        return report
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit assessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{user_id}", response_model=List[AssessmentReport])
async def get_assessment_history(user_id: str):
    """Retrieve historical assessment reports for a student."""
    from app.main import assessment_service

    if not assessment_service:
        raise HTTPException(status_code=503, detail="Assessment service not ready")

    return assessment_service.get_user_reports(user_id)
