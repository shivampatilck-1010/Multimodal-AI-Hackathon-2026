"""Tutor routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.tutor.models import TutorAnswer

router = APIRouter()

class AskRequest(BaseModel):
    session_id: str
    query: str
    level: str = "intermediate"
    course_id: str = "hackathon_course"

@router.post("/ask", response_model=TutorAnswer)
async def ask_tutor(request: AskRequest):
    from app.main import tutor_service
    
    if not tutor_service:
        raise HTTPException(status_code=503, detail="Tutor service not ready")
        
    try:
        answer = tutor_service.ask(request.session_id, request.query, request.level, request.course_id)
        return answer
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
