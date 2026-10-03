"""Knowledge base routes."""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List

from app.tutor.models import ContentUnit

router = APIRouter()

class IngestRequest(BaseModel):
    units: List[ContentUnit]

@router.post("/ingest")
async def ingest_content(request: IngestRequest, background_tasks: BackgroundTasks):
    from app.main import kb
    
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")
        
    try:
        # Ingest might take time (embedding), so we could do it in background, 
        # but for hackathon we can block or just return success and do background.
        # Let's do it inline to ensure it's ready.
        added = kb.add_units(request.units)
        return {"status": "success", "chunks_added": added, "total_chunks": sum(kb.courses().values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_kb():
    from app.main import kb
    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")
    for course_id in kb.courses().keys():
        kb.delete_course(course_id)
    return {"status": "success", "total_chunks": 0}
