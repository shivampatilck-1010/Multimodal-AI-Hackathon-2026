"""Master Ingestion Pipeline for Multimodal Course Materials.

Orchestrates PDF, PPTX, and Video parsing, figure understanding, semantic chunking,
taxonomy discovery, prerequisite graph assembly, and KB vector indexing.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.tutor.knowledge_base import KnowledgeBase
from app.tutor.models import ContentUnit
from app.kb.models import FigureUnit, ConceptNode, IngestSummary, CourseKnowledgeGraph
from app.kb.media_store import MediaStore
from app.kb.graph_store import GraphStore

from app.ingestion.parsers.pdf_parser import PdfParser
from app.ingestion.parsers.ppt_parser import PptParser
from app.ingestion.parsers.video_parser import VideoParser
from app.ingestion.vision.diagram_analyzer import DiagramAnalyzer
from app.ingestion.chunking.semantic_chunker import SemanticChunker
from app.ingestion.taxonomy.concept_extractor import ConceptExtractor
from app.ingestion.taxonomy.prerequisite_graph import PrerequisiteGraphBuilder

logger = logging.getLogger(__name__)

SUPPORTED_PDF_EXTS = {".pdf"}
SUPPORTED_PPT_EXTS = {".pptx", ".ppt"}
SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav", ".m4a"}


class IngestionPipeline:
    """End-to-end multimodal ingestion pipeline for Member 1."""

    def __init__(
        self,
        kb: KnowledgeBase,
        media_store: MediaStore,
        graph_store: GraphStore,
        api_key: str | None = None,
    ) -> None:
        self.kb = kb
        self.media_store = media_store
        self.graph_store = graph_store
        self.api_key = api_key

        # Subcomponents
        self.pdf_parser = PdfParser(media_store=self.media_store)
        self.ppt_parser = PptParser(media_store=self.media_store)
        self.video_parser = VideoParser()
        self.diagram_analyzer = DiagramAnalyzer(api_key=self.api_key)
        self.chunker = SemanticChunker()
        self.concept_extractor = ConceptExtractor(api_key=self.api_key)
        self.graph_builder = PrerequisiteGraphBuilder(api_key=self.api_key)

    def ingest_file(
        self,
        course_id: str,
        file_path: Path | str,
        subtitle_path: Path | str | None = None,
    ) -> IngestSummary:
        """Ingest a single course file (PDF, PPTX, or Video/Audio)."""
        path = Path(file_path)
        if not path.exists():
            return IngestSummary(
                course_id=course_id,
                errors=[f"File does not exist: {path}"],
            )

        ext = path.suffix.lower()
        all_units: list[ContentUnit] = []
        all_figures: list[FigureUnit] = []
        errors: list[str] = []

        try:
            # 1. Parse by modality
            if ext in SUPPORTED_PDF_EXTS:
                pdf_res = self.pdf_parser.parse(path, course_id=course_id)
                all_figures.extend(pdf_res.figures)
                units = self.chunker.chunk_pdf(pdf_res)
                all_units.extend(units)

            elif ext in SUPPORTED_PPT_EXTS:
                ppt_res = self.ppt_parser.parse(path, course_id=course_id)
                all_figures.extend(ppt_res.figures)
                units = self.chunker.chunk_pptx(ppt_res)
                all_units.extend(units)

            elif ext in SUPPORTED_VIDEO_EXTS:
                vid_res = self.video_parser.parse(
                    path, course_id=course_id, subtitle_path=subtitle_path
                )
                units = self.chunker.chunk_video(vid_res)
                all_units.extend(units)

            else:
                errors.append(f"Unsupported file format: {ext}")
                return IngestSummary(
                    course_id=course_id,
                    files_processed=[],
                    errors=errors,
                )

            # 2. Analyze diagrams & figures if present
            for fig in all_figures:
                img_path = self.media_store.get_image_path(fig.image_rel_path)
                context_hint = ""
                # Find matching chunk text for context
                for u in all_units:
                    if fig.id in u.metadata.get("figure_ids", []):
                        context_hint = u.text
                        break
                self.diagram_analyzer.analyze_figure(fig, img_path, context_hint)

            # 3. Extract curriculum taxonomy & tag content units
            tagged_units, nodes, hierarchy = self.concept_extractor.extract_taxonomy(
                course_id=course_id,
                units=all_units,
                figures=all_figures,
            )

            # 4. Discover prerequisite dependencies and build graph
            graph = self.graph_builder.build_graph(
                course_id=course_id,
                nodes=nodes,
                hierarchy=hierarchy,
            )
            self.graph_store.save_graph(graph)

            # 5. Index content units into Knowledge Base vector store
            if tagged_units:
                self.kb.add_units(tagged_units)

            return IngestSummary(
                course_id=course_id,
                files_processed=[path.name],
                units_count=len(tagged_units),
                figures_count=len(all_figures),
                concepts_count=len(nodes),
                prerequisites_count=len(graph.edges),
                errors=errors,
            )

        except Exception as e:
            logger.error(f"failed_ingesting_{path.name}: {e}", exc_info=True)
            return IngestSummary(
                course_id=course_id,
                files_processed=[path.name],
                errors=[str(e)],
            )

    def ingest_directory(
        self,
        course_id: str,
        dir_path: Path | str,
    ) -> IngestSummary:
        """Ingest all supported files in a directory."""
        dir_p = Path(dir_path)
        if not dir_p.is_dir():
            return IngestSummary(course_id=course_id, errors=[f"Not a directory: {dir_p}"])

        all_files: list[Path] = []
        for p in dir_p.rglob("*"):
            if p.is_file() and p.suffix.lower() in (
                SUPPORTED_PDF_EXTS | SUPPORTED_PPT_EXTS | SUPPORTED_VIDEO_EXTS
            ):
                all_files.append(p)

        summary = IngestSummary(course_id=course_id)
        for f in all_files:
            sub = self.ingest_file(course_id=course_id, file_path=f)
            summary.files_processed.extend(sub.files_processed)
            summary.units_count += sub.units_count
            summary.figures_count += sub.figures_count
            summary.concepts_count += sub.concepts_count
            summary.prerequisites_count += sub.prerequisites_count
            summary.errors.extend(sub.errors)

        return summary
