"""Tests for the grounding and citation components."""

import pytest
from app.tutor.models import RetrievedChunk, ContentUnit, PdfSource, VideoSource
from app.tutor.grounding import EvidenceGate
from app.tutor.citations import CitationValidator

def test_evidence_gate():
    gate = EvidenceGate(min_score=0.5, min_chunks=1, min_term_coverage=0.2)
    
    # Low score
    chunks = [
        RetrievedChunk(chunk_id="chunk-1", course_id="course-1", unit_id="1", text="some text", score=0.4, source=PdfSource(type="pdf", file_name="doc.pdf", page=1))
    ]
    res = gate.evaluate("query about things", chunks)
    assert not res.sufficient
    assert "best score 0.400 < 0.500" in res.reason
    
    # Good score, good coverage
    chunks = [
        RetrievedChunk(chunk_id="chunk-2", course_id="course-1", unit_id="2", text="The Krebs cycle produces energy.", score=0.8, source=VideoSource(type="video", file_name="vid.mp4", timestamp_start="00:10"))
    ]
    res = gate.evaluate("krebs cycle energy", chunks)
    assert res.sufficient
    assert res.top_score == 0.8
    assert res.term_coverage == 1.0

def test_citation_validator():
    validator = CitationValidator()
    
    # Mock chunks
    chunk1 = RetrievedChunk(chunk_id="chunk-1", course_id="course-1", unit_id="1", text="Biology is fun.", score=0.9, source=PdfSource(type="pdf", file_name="doc.pdf", page=1))
    
    # Validate with missing citations (hallucinated)
    model_output = {
        "grounded": True,
        "answer": "Biology is fun [S1] and physics [S2]",
        "cited_sources": ["S1", "S2"]
    }
    evidence = {"S1": chunk1}
    
    val_result = validator.validate(course_id="course-1", model_output=model_output, evidence=evidence)
    
    # S1 is mapped to index 0, S2 is hallucinated (or not in evidence)
    assert len(val_result.citations) == 1
    assert val_result.citations[0].file_name == "doc.pdf"
    assert "[S1]" in val_result.answer  # S1 is kept
    assert "[S2]" not in val_result.answer # S2 stripped
