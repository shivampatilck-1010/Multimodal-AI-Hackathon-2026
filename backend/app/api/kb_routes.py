"""Knowledge Base API routes for ingestion, retrieval, figures, concepts and source files."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote

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


# -------------------------------------------------------------
# Shared helpers
# -------------------------------------------------------------

def _get_data_dir() -> Path:
    """Return the configured data directory."""
    from app.config import get_settings

    return Path(get_settings().data_dir).resolve()


def _safe_course_dir(course_id: str) -> Path:
    """Resolve a course directory and prevent path traversal."""
    data_dir = _get_data_dir()
    candidate = (data_dir / course_id).resolve()

    if candidate != data_dir and data_dir not in candidate.parents:
        raise HTTPException(status_code=400, detail="Invalid course identifier")

    return candidate


def _find_source_file(course_id: str, source_id: str) -> Path:
    """
    Resolve a source file from the course data directory.

    Supports files stored directly in the course directory and in its
    common source/material subdirectories. Only files contained within
    the configured data directory are eligible for serving.
    """
    data_dir = _get_data_dir()
    course_dir = _safe_course_dir(course_id)

    if not course_dir.exists() or not course_dir.is_dir():
        raise HTTPException(status_code=404, detail="Course source directory not found")

    decoded_source_id = unquote(source_id).strip()
    if not decoded_source_id or decoded_source_id in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid source identifier")

    # Reject paths, traversal sequences and absolute paths.
    source_path = Path(decoded_source_id)
    if source_path.is_absolute() or len(source_path.parts) != 1:
        raise HTTPException(status_code=400, detail="Invalid source identifier")

    if "/" in decoded_source_id or "\\" in decoded_source_id or ".." in decoded_source_id:
        raise HTTPException(status_code=400, detail="Invalid source identifier")

    allowed_roots = [
        course_dir,
        course_dir / "sources",
        course_dir / "materials",
        course_dir / "uploads",
    ]

    for root in allowed_roots:
        try:
            root_resolved = root.resolve()
            if root_resolved != data_dir and data_dir not in root_resolved.parents:
                continue
        except OSError:
            continue

        candidate = (root / decoded_source_id).resolve()

        if candidate != data_dir and data_dir not in candidate.parents:
            continue

        if candidate.is_file():
            return candidate

    raise HTTPException(
        status_code=404,
        detail=f"Source file '{decoded_source_id}' not found for course '{course_id}'",
    )


# -------------------------------------------------------------
# 1. Ingestion
# -------------------------------------------------------------

@router.post("/ingest")
async def ingest_content(request: IngestRequest):
    """Ingest content units and build or update the course knowledge graph."""
    from app.main import kb, ingestion_pipeline, graph_store

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    if not request.units:
        raise HTTPException(status_code=400, detail="No content units provided")

    course_ids = {unit.course_id for unit in request.units}
    if len(course_ids) != 1:
        raise HTTPException(
            status_code=400,
            detail="All units in one ingestion request must belong to the same course",
        )

    try:
        kb.add_units(request.units)

        course_id = request.units[0].course_id

        if ingestion_pipeline and graph_store:
            tagged, nodes, hierarchy = ingestion_pipeline.concept_extractor.extract_taxonomy(
                course_id,
                request.units,
            )
            graph = ingestion_pipeline.graph_builder.build_graph(
                course_id,
                nodes,
                hierarchy,
            )
            graph_store.save_graph(graph)

        return {
            "status": "success",
            "course_id": course_id,
            "units_ingested": len(request.units),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    course_id: str = Form(...),
):
    """Save an uploaded source file to the configured course directory."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no filename")

    filename = Path(file.filename).name
    if filename in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")

    course_dir = _safe_course_dir(course_id)
    course_dir.mkdir(parents=True, exist_ok=True)

    destination = (course_dir / filename).resolve()
    data_dir = _get_data_dir()

    if destination != data_dir and data_dir not in destination.parents:
        raise HTTPException(status_code=400, detail="Invalid upload destination")

    try:
        with destination.open("wb") as output:
            shutil.copyfileobj(file.file, output)
    except OSError as exc:
        raise HTTPException(status_code=500, detail="Could not save uploaded file") from exc
    finally:
        await file.close()

    return {
        "status": "success",
        "course_id": course_id,
        "file_name": filename,
    }


# -------------------------------------------------------------
# 2. Courses and content units
# -------------------------------------------------------------

@router.get("/courses")
async def list_courses():
    """List courses available in the knowledge base."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    return [
        {"course_id": course_id, "unit_count": count}
        for course_id, count in kb.courses().items()
    ]


@router.get("/courses/{course_id}/units")
async def list_course_units(course_id: str):
    """Return content units belonging to a course."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    units = kb.get_course_units(course_id)
    if units is None:
        return []

    return units


# -------------------------------------------------------------
# 3. Retrieval and figures
# -------------------------------------------------------------

@router.get("/search", response_model=List[RetrievedChunk])
async def search_content(
    course_id: str,
    query: str,
    top_k: int = 5,
):
    """Retrieve relevant course chunks for a query."""
    from app.main import kb

    if not kb:
        raise HTTPException(status_code=503, detail="Knowledge base not ready")

    if not query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if not 1 <= top_k <= 50:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 50")

    try:
        results = kb.search(course_id=course_id, query=query, top_k=top_k)
        return results
    except AttributeError:
        raise HTTPException(
            status_code=501,
            detail="Knowledge base search interface is not configured",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


@router.get("/courses/{course_id}/figures", response_model=List[FigureUnit])
async def list_course_figures(course_id: str):
    """List figures indexed for a course."""
    from app.main import media_store

    if not media_store:
        raise HTTPException(status_code=503, detail="Media store not ready")

    figures = media_store.get_course_figures(course_id)
    return figures or []


@router.get("/courses/{course_id}/figures/{figure_id}", response_model=FigureUnit)
async def get_figure(course_id: str, figure_id: str):
    """Return metadata for one figure."""
    from app.main import media_store

    if not media_store:
        raise HTTPException(status_code=503, detail="Media store not ready")

    figure = media_store.get_figure(course_id, figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail="Figure not found")

    return figure


@router.get("/courses/{course_id}/figures/{figure_id}/image")
async def get_figure_image(course_id: str, figure_id: str):
    """Serve an indexed figure image."""
    from app.main import media_store

    if not media_store:
        raise HTTPException(status_code=503, detail="Media store not ready")

    figure = media_store.get_figure(course_id, figure_id)
    if not figure:
        raise HTTPException(status_code=404, detail="Figure not found")

    image_path = media_store.get_image_path(figure.image_rel_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image file missing on disk")

    return FileResponse(str(image_path))


# -------------------------------------------------------------
# 4. Concepts and evidence
# -------------------------------------------------------------

@router.get("/courses/{course_id}/concepts", response_model=List[ConceptNode])
async def list_course_concepts(course_id: str):
    """Return concepts identified in course materials."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        return []

    return list(graph.nodes.values())


@router.get("/courses/{course_id}/concepts/{concept_id}/evidence")
async def get_concept_evidence(course_id: str, concept_id: str):
    """Return a concept and its supporting content units and figures."""
    from app.main import kb, media_store, graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph or concept_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Concept not found")

    concept = graph.nodes[concept_id]

    units = []
    if kb:
        for unit_id in concept.content_unit_ids:
            unit = kb.get_unit(course_id, unit_id)
            if unit is not None:
                units.append(unit)

    figures = []
    if media_store:
        for figure_id in concept.figure_ids:
            figure = media_store.get_figure(course_id, figure_id)
            if figure is not None:
                figures.append(figure)

    return {
        "concept": concept,
        "units": units,
        "figures": figures,
    }


# -------------------------------------------------------------
# 5. Knowledge graph
# -------------------------------------------------------------

@router.get("/courses/{course_id}/prerequisites", response_model=CourseKnowledgeGraph)
async def get_prerequisites(course_id: str):
    """Return the prerequisite graph for a course."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")

    return graph


@router.get("/courses/{course_id}/learning_path")
async def get_learning_path(course_id: str, concept_id: Optional[str] = None):
    """Return an ordered learning path, optionally starting from a concept."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")

    if concept_id is not None and concept_id not in graph.nodes:
        raise HTTPException(status_code=404, detail="Concept not found")

    if concept_id is None:
        return graph.get_learning_path()

    return graph.get_learning_path(concept_id)


@router.get("/courses/{course_id}/hierarchy")
async def get_concept_hierarchy(course_id: str):
    """Return the concept hierarchy for a course."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")

    return graph.hierarchy


@router.get("/courses/{course_id}/flowchart")
async def get_flowchart(course_id: str):
    """Return graph nodes and edges for flowchart visualization."""
    from app.main import graph_store

    if not graph_store:
        raise HTTPException(status_code=503, detail="Graph store not ready")

    graph = graph_store.get_graph(course_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Knowledge graph not found")

    return {
        "nodes": list(graph.nodes.values()),
        "edges": graph.edges,
    }


# -------------------------------------------------------------
# 6. Source files — used by tutor citation links
# -------------------------------------------------------------


@router.get("/courses/{course_id}/sources/{source_id}")
async def get_source_file(course_id: str, source_id: str):
    source_path = _find_source_file(course_id, source_id)
    return FileResponse(
        path=str(source_path),
        filename=source_path.name,
        content_disposition_type="inline",
    )
