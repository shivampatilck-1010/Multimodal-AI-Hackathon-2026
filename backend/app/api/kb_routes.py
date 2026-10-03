"""Knowledge Base API routes for ingestion, figures, concepts, and prerequisites.

Serves data contracts to Member 2 (retrieval), Member 3 (assessment grounding),
and Member 4 (learner model mastery graph).
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.tutor.models import ContentUnit, RetrievedChunk
from app.kb.models import (
    FigureUnit,
    ConceptNode,
    CourseKnowledgeGraph,
    IngestSummary,
)

router = APIRouter()


class IngestRequest(BaseModel):
    units: List[ContentUnit]


# ------------------------------------------------------------- 1. Ingestion
@router.post("/ingest")
async def ingest_content(request: IngestRequest):
    """Direct batch ingestion of ContentUnits (Member 2 contract)."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    try:
        added = kb.add_units(request.units)
        return {
            "status": "success",
            "chunks_added": added,
            "total_chunks": sum(kb.courses().values()),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload", response_model=IngestSummary)
async def upload_course_file(
    course_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload and ingest a raw course file (PDF, PPTX, or Video/Audio)."""
    from app.main import ingestion_pipeline
    from app.config import get_settings

    if not ingestion_pipeline:
        raise HTTPException(status_code=503, detail="Ingestion pipeline not ready")

    settings = get_settings()
    upload_dir = settings.data_dir / "uploads" / course_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    dest_path = upload_dir / file.filename
    try:
        with dest_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        summary = ingestion_pipeline.ingest_file(
            course_id=course_id,
            file_path=dest_path,
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------- 2. Retrieval & Units
@router.get("/courses")
async def list_courses():
    """List all available courses and their chunk counts."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")
    return {"courses": kb.courses()}


@router.get("/courses/{course_id}/units", response_model=List[ContentUnit])
async def list_course_units(course_id: str):
    """Retrieve all content units for a given course."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")
    return kb.list_units(course_id)


@router.get("/search", response_model=List[RetrievedChunk])
async def search_knowledge_base(
    course_id: str,
    query: str,
    top_k: int = 6,
    topic: Optional[str] = None,
    concept: Optional[str] = None,
):
    """Search knowledge base with cosine similarity and optional topic/concept filters."""
    from app.main import kb
    from app.tutor.retriever import Retriever
    from app.tutor.models import RetrievalFilters

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    retriever = Retriever(store=kb.store, embedder=kb.embedder, default_top_k=top_k)
    filters = None
    if topic or concept:
        filters = RetrievalFilters(
            topics=[topic] if topic else None,
            concepts=[concept] if concept else None,
        )

    results = retriever.retrieve(
        course_id=course_id,
        query=query,
        top_k=top_k,
        filters=filters,
    )
    return results


# ------------------------------------------------------------- 3. Figures & Diagrams
@router.get("/courses/{course_id}/figures", response_model=List[FigureUnit])
async def list_course_figures(course_id: str):
    """List all extracted diagrams and figures for a course."""
    from app.main import media_store

    if not media_store:
        raise HTTPException(status_code=503, detail="Media store not ready")
    return media_store.list_figures(course_id)


@router.get("/figures/{course_id}/{figure_id}", response_model=FigureUnit)
async def get_figure_metadata(course_id: str, figure_id: str):
    """Fetch metadata and explanation for a specific figure."""
    from app.main import media_store

    if not media_store:
        raise HTTPException(status_code=503, detail="Media store not ready")
    fig = media_store.get_figure(course_id, figure_id)
    if not fig:
        raise HTTPException(status_code=404, detail="Figure not found")
    return fig


@router.get("/figures/{course_id}/{figure_id}/image")
async def get_figure_image(course_id: str, figure_id: str):
    """Stream image bytes for an extracted figure."""
    from app.main import media_store

    if not media_store:
        raise HTTPException(status_code=503, detail="Media store not ready")
    fig = media_store.get_figure(course_id, figure_id)
    if not fig:
        raise HTTPException(status_code=404, detail="Figure not found")
    img_path = media_store.get_image_path(fig.image_rel_path)
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing on disk")
    return FileResponse(str(img_path))


# ------------------------------------------------------------- 4. Concepts (Member 3 Contract)
@router.get("/courses/{course_id}/concepts", response_model=List[ConceptNode])
async def list_course_concepts(course_id: str):
    """Return all concepts identified in course materials (for question scoping)."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")
    graph = graph_store.get_graph(course_id)
    if not graph:
        return []
    return list(graph.nodes.values())


@router.get("/courses/{course_id}/concepts/{concept_id}/evidence")
async def get_concept_evidence(course_id: str, concept_id: str):
    """Fetch complete source evidence, figures, and definitions for a concept (for MCQ generation)."""
    from app.main import kb, media_store, graph_store

    if not kb or not graph_store or not media_store:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    graph = graph_store.get_graph(course_id)
    if not graph or concept_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Concept not found in course")

    concept = graph.nodes[concept_id]

    # Retrieve all linked content units
    units = [
        kb.get_unit(course_id, uid)
        for uid in concept.content_unit_ids
        if kb.get_unit(course_id, uid) is not None
    ]

    # Retrieve all linked figures
    figures = [
        media_store.get_figure(course_id, fid)
        for fid in concept.figure_ids
        if media_store.get_figure(course_id, fid) is not None
    ]

    return {
        "concept": concept,
        "units": units,
        "figures": figures,
    }


# ------------------------------------------------------------- 5. Prerequisites (Member 4 Contract)
@router.get("/courses/{course_id}/prerequisites", response_model=CourseKnowledgeGraph)
async def get_course_prerequisites(course_id: str):
    """Return the complete concept prerequisite DAG and topological ordering for mastery tracking."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        return CourseKnowledgeGraph(course_id=course_id, nodes={}, edges=[])
    return graph


@router.get("/courses/{course_id}/learning_path")
async def get_course_learning_path(course_id: str):
    """Return concepts in pedagogical topological sort order (prerequisites first)."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    order = graph_store.get_topological_order(course_id)
    graph = graph_store.get_graph(course_id)
    ordered_concepts = [graph.nodes[cid] for cid in order if graph and cid in graph.nodes]
    return {
        "course_id": course_id,
        "learning_path": ordered_concepts,
    }


@router.get("/courses/{course_id}/hierarchy")
async def get_course_hierarchy(course_id: str):
    """Return Topic -> Subtopic -> Concepts hierarchy for learner mastery dashboards."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        return {"course_id": course_id, "topics": {}}
    return {
        "course_id": course_id,
        "topics": graph.topics_hierarchy,
    }


# ------------------------------------------------------------- 6. Administration
@router.delete("/clear")
async def clear_kb():
    """Clear all courses and knowledge base units."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")
    for course_id in list(kb.courses().keys()):
        kb.delete_course(course_id)
    return {"status": "success", "total_chunks": 0}
