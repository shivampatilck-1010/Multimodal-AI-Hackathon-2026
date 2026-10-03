"""Tests for Member 1 Multimodal Knowledge Base Ingestion Pipeline."""

import tempfile
from pathlib import Path
from PIL import Image

from app.tutor.models import PdfSource, SlideSource, VideoSource, ContentUnit
from app.kb.models import (
    BoundingBox,
    FigureUnit,
    ConceptNode,
    PrerequisiteEdge,
    CourseKnowledgeGraph,
)
from app.kb.graph_store import GraphStore
from app.kb.media_store import MediaStore
from app.ingestion.chunking.semantic_chunker import SemanticChunker
from app.ingestion.parsers.pdf_parser import ExtractedPage, PdfParseResult
from app.ingestion.parsers.ppt_parser import ExtractedSlide, PptParseResult
from app.ingestion.parsers.video_parser import (
    VideoParser,
    VideoParseResult,
    VideoTranscriptSegment,
)
from app.ingestion.taxonomy.concept_extractor import ConceptExtractor


def test_models_provenance():
    # 1. PDF Figure Unit
    pdf_fig = FigureUnit(
        id="fig_test_p1_1",
        course_id="test_course",
        source=PdfSource(type="pdf", file_name="lecture1.pdf", page=5),
        image_rel_path="test_course/fig_test_p1_1.png",
        caption="Diagram of Cell Structure",
        explanation="Shows mitochondria and chloroplasts.",
        associated_concepts=["Cell Structure", "Organelles"],
        bounding_box=BoundingBox(x0=10.0, y0=20.0, x1=200.0, y1=150.0),
    )
    assert pdf_fig.source.page == 5
    assert pdf_fig.source.location_label() == "Page 5"

    # 2. Slide Figure Unit
    slide_fig = FigureUnit(
        id="fig_test_s3_1",
        course_id="test_course",
        source=SlideSource(type="slide", file_name="deck.pptx", slide=3),
        image_rel_path="test_course/fig_test_s3_1.png",
        caption="Photosynthesis Overview",
    )
    assert slide_fig.source.slide == 3
    assert slide_fig.source.location_label() == "Slide 3"

    # 3. Video Provenance
    vid_source = VideoSource(
        type="video",
        file_name="lecture.mp4",
        timestamp_start="01:15",
        timestamp_end="02:30",
    )
    assert vid_source.start_seconds == 75
    assert vid_source.end_seconds == 150
    assert vid_source.location_label() == "00:01:15 - 00:02:30"


def test_graph_store_acyclic_and_topological_sort():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = GraphStore(persist_dir=Path(tmpdir))

        nodes = {
            "c_math": ConceptNode(
                id="c_math",
                course_id="cs101",
                name="Basic Math",
                topic="Prerequisites",
                summary="Arithmetic and algebra.",
            ),
            "c_algo": ConceptNode(
                id="c_algo",
                course_id="cs101",
                name="Algorithms",
                topic="Computer Science",
                summary="Algorithmic problem solving.",
            ),
            "c_ml": ConceptNode(
                id="c_ml",
                course_id="cs101",
                name="Machine Learning",
                topic="AI",
                summary="Statistical learning models.",
            ),
        }

        # Dependencies: Math -> Algo -> ML
        # Introduce an intentional cycle to test cycle resolution: ML -> Math (weaker strength 0.2)
        edges = [
            PrerequisiteEdge(
                source_concept_id="c_math",
                target_concept_id="c_algo",
                strength=0.9,
            ),
            PrerequisiteEdge(
                source_concept_id="c_algo",
                target_concept_id="c_ml",
                strength=0.9,
            ),
            PrerequisiteEdge(
                source_concept_id="c_ml",
                target_concept_id="c_math",
                strength=0.2,  # cycle back to math
            ),
        ]

        graph = CourseKnowledgeGraph(
            course_id="cs101",
            nodes=nodes,
            edges=edges,
        )

        store.save_graph(graph)

        clean = store.get_graph("cs101")
        assert clean is not None

        # Verify cycle was broken
        assert len(clean.edges) == 2
        remaining_edges = {(e.source_concept_id, e.target_concept_id) for e in clean.edges}
        assert ("c_math", "c_algo") in remaining_edges
        assert ("c_algo", "c_ml") in remaining_edges
        assert ("c_ml", "c_math") not in remaining_edges

        # Verify topological learning path
        order = store.get_topological_order("cs101")
        assert order == ["c_math", "c_algo", "c_ml"]

        # Ancestors of ML should include Math and Algo
        ancestors = store.get_all_ancestor_prerequisites("cs101", "c_ml")
        assert "c_math" in ancestors
        assert "c_algo" in ancestors


def test_semantic_chunker():
    chunker = SemanticChunker(max_chunk_chars=500, video_target_duration_seconds=30)

    # 1. Test PDF chunking
    pdf_res = PdfParseResult(
        file_name="bio.pdf",
        course_id="bio101",
        total_pages=2,
        pages=[
            ExtractedPage(
                page_number=1,
                text="Photosynthesis converts solar light into chemical bond energy.",
                figures=[],
            ),
            ExtractedPage(
                page_number=2,
                text="The Calvin cycle takes place inside the chloroplast stroma.",
                figures=[],
            ),
        ],
        figures=[],
    )
    pdf_units = chunker.chunk_pdf(pdf_res)
    assert len(pdf_units) == 2
    assert pdf_units[0].source.page == 1
    assert pdf_units[1].source.page == 2
    assert "Photosynthesis" in pdf_units[0].text

    # 2. Test PPTX chunking
    ppt_res = PptParseResult(
        file_name="deck.pptx",
        course_id="bio101",
        total_slides=1,
        slides=[
            ExtractedSlide(
                slide_number=1,
                title="Cellular Respiration",
                body_text="Glycolysis breaks glucose into pyruvate.",
                speaker_notes="Emphasize ATP yield.",
                full_text="## Cellular Respiration\n\nGlycolysis breaks glucose into pyruvate.\n\n[Speaker Notes: Emphasize ATP yield.]",
                figures=[],
            )
        ],
        figures=[],
    )
    ppt_units = chunker.chunk_pptx(ppt_res)
    assert len(ppt_units) == 1
    assert ppt_units[0].source.slide == 1
    assert "Glycolysis" in ppt_units[0].text
    assert ppt_units[0].metadata["has_notes"] is True

    # 3. Test Video chunking
    vid_segments = [
        VideoTranscriptSegment(
            start_seconds=0,
            end_seconds=15,
            timestamp_start="00:00:00",
            timestamp_end="00:00:15",
            text="Welcome to biology lecture 1.",
        ),
        VideoTranscriptSegment(
            start_seconds=15,
            end_seconds=35,
            timestamp_start="00:00:15",
            timestamp_end="00:00:35",
            text="Today we talk about energy systems in organisms.",
        ),
    ]
    vid_res = VideoParseResult(
        file_name="lecture1.mp4",
        course_id="bio101",
        duration_seconds=35,
        segments=vid_segments,
        full_transcript="...",
    )
    vid_units = chunker.chunk_video(vid_res)
    assert len(vid_units) >= 1
    assert vid_units[0].source.type == "video"
    assert vid_units[0].source.start_seconds == 0


def test_video_subtitle_parser():
    parser = VideoParser()
    sample_vtt = """WEBVTT

00:00:10.000 --> 00:00:25.000
Photosynthesis begins in the thylakoid membranes.

00:00:25.000 --> 00:00:50.000
Photons excite electrons in chlorophyll molecules.
"""
    segments = parser._parse_vtt(sample_vtt)
    assert len(segments) == 2
    assert segments[0].start_seconds == 10
    assert segments[0].end_seconds == 25
    assert segments[0].timestamp_start == "00:00:10"
    assert "thylakoid" in segments[0].text
    assert segments[1].start_seconds == 25
    assert segments[1].end_seconds == 50


def test_concept_tagging():
    extractor = ConceptExtractor()
    units = [
        ContentUnit(
            id="u1",
            course_id="bio101",
            text="Photosynthesis is the fundamental conversion of sunlight.",
            source=PdfSource(type="pdf", file_name="bio.pdf", page=1),
            metadata={"title": "Photosynthesis Process"},
        ),
        ContentUnit(
            id="u2",
            course_id="bio101",
            text="The Calvin cycle produces glucose in the dark reactions.",
            source=PdfSource(type="pdf", file_name="bio.pdf", page=2),
            metadata={"title": "Calvin Cycle"},
        ),
    ]

    tagged_units, nodes, hierarchy = extractor.extract_taxonomy("bio101", units)
    assert len(tagged_units) == 2
    assert len(nodes) >= 1
    assert tagged_units[0].topic is not None
    assert tagged_units[0].concept is not None
