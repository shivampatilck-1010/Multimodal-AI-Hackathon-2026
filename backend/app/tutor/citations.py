"""Citation validation.

The LLM is never trusted to produce source metadata. It may only reference the
opaque labels (S1..Sn) of evidence it was shown. This module:

  1. extracts the labels the model used (inline markers + ``cited_sources``),
  2. rejects labels that do not map to a retrieved chunk of the same course,
  3. removes rejected markers from the answer text,
  4. redacts page / slide / timestamp / filename mentions that do not match the
     retrieved evidence (defence in depth against invented locations),
  5. builds every ``Citation`` from the retrieved chunk's stored metadata,
  6. downgrades "grounded" answers that end up with zero valid citations.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, urlencode

from app.tutor.models import Citation, RetrievedChunk, format_timestamp, parse_timestamp

_INLINE_MARKER_RE = re.compile(r"\[\s*([A-Za-z]{1,10}\s*\d{1,4}(?:\s*[,;]\s*[A-Za-z]{1,10}\s*\d{1,4})*)\s*\]")
_LABEL_RE = re.compile(r"^[Ss](\d{1,4})$")
_PAGE_RE = re.compile(r"\b(?:pages?|pg\.?|pp?\.)\s*(\d{1,5})\b", re.IGNORECASE)
_SLIDE_RE = re.compile(r"\bslides?\s*(?:no\.?|number|#)?\s*(\d{1,4})\b", re.IGNORECASE)
_TIMESTAMP_RE = re.compile(r"\b\d{1,2}:\d{2}:\d{2}\b")
_FILENAME_RE = re.compile(
    r"\b[\w\-.]+\.(?:pdf|pptx?|key|mp4|mov|mkv|webm|m4a|mp3|wav|docx?)\b", re.IGNORECASE
)
REDACTION = "[unverified reference removed]"
EXCERPT_CHARS = 400


def normalize_label(raw: str) -> str | None:
    m = _LABEL_RE.match(raw.strip().replace(" ", ""))
    return f"S{int(m.group(1))}" if m else None


def build_source_link(course_id: str, chunk: RetrievedChunk, template: str) -> str:
    base = template.format(
        course_id=quote(course_id, safe=""),
        source_id=quote(chunk.source.document_key, safe=""),
    )
    query = {**chunk.source.link_query(), "chunk": chunk.chunk_id}
    return f"{base}?{urlencode(query)}"


def build_citation(label: str, chunk: RetrievedChunk, link_template: str) -> Citation:
    """Construct a citation purely from retrieved metadata. Public: Member 3 reuses it."""
    src = chunk.source
    excerpt = chunk.text if len(chunk.text) <= EXCERPT_CHARS else chunk.text[:EXCERPT_CHARS].rstrip() + "..."
    return Citation(
        label=label,
        source_id=chunk.chunk_id,
        course_id=chunk.course_id,
        source_type=src.type,
        file_name=src.file_name,
        file_id=src.file_id,
        page=getattr(src, "page", None),
        slide=getattr(src, "slide", None),
        timestamp_start=getattr(src, "timestamp_start", None),
        timestamp_end=getattr(src, "timestamp_end", None),
        start_seconds=getattr(src, "start_seconds", None),
        location=src.location_label(),
        link=build_source_link(chunk.course_id, chunk, link_template),
        topic=chunk.topic,
        concept=chunk.concept,
        excerpt=excerpt,
    )


@dataclass
class CitationValidationResult:
    answer: str
    grounded: bool
    citations: list[Citation]
    llm_labels: list[str] = field(default_factory=list)
    rejected_labels: list[str] = field(default_factory=list)
    redacted_mentions: list[str] = field(default_factory=list)
    downgrade_reason: str | None = None


class CitationValidator:
    def __init__(self, link_template: str = "/courses/{course_id}/sources/{source_id}") -> None:
        self.link_template = link_template

    def validate(
        self,
        *,
        course_id: str,
        model_output: dict[str, Any],
        evidence: dict[str, RetrievedChunk],
    ) -> CitationValidationResult:
        # Only evidence belonging to the requested course is citable.
        evidence = {lbl: c for lbl, c in evidence.items() if c.course_id == course_id}

        answer = str(model_output.get("answer") or "").strip()
        model_grounded = bool(model_output.get("grounded"))
        declared = model_output.get("cited_sources") or []
        if not isinstance(declared, list):
            declared = []

        llm_labels: list[str] = []
        rejected: list[str] = []
        ordered_valid: list[str] = []

        def _accept(raw: str) -> str | None:
            raw = str(raw)
            if raw not in llm_labels:
                llm_labels.append(raw)
            label = normalize_label(raw)
            if label is None or label not in evidence:
                if raw not in rejected:
                    rejected.append(raw)
                return None
            if label not in ordered_valid:
                ordered_valid.append(label)
            return label

        def _rewrite_marker(match: re.Match[str]) -> str:
            kept = [lbl for part in re.split(r"[,;]", match.group(1)) if (lbl := _accept(part.strip()))]
            return "".join(f"[{lbl}]" for lbl in kept)

        answer = _INLINE_MARKER_RE.sub(_rewrite_marker, answer)
        for raw in declared:
            _accept(raw)

        answer, redacted = self._redact_unverified_mentions(answer, list(evidence.values()))
        answer = re.sub(r"[ \t]{2,}", " ", answer).replace(" .", ".").strip()

        citations = [build_citation(lbl, evidence[lbl], self.link_template) for lbl in ordered_valid]

        downgrade = None
        grounded = model_grounded
        if model_grounded and not answer:
            grounded, downgrade = False, "The model returned an empty answer."
        elif model_grounded and not citations:
            grounded, downgrade = False, "The generated answer contained no verifiable citations to course evidence."
        if not grounded:
            citations = []

        return CitationValidationResult(
            answer=answer,
            grounded=grounded,
            citations=citations,
            llm_labels=llm_labels,
            rejected_labels=rejected,
            redacted_mentions=redacted,
            downgrade_reason=downgrade,
        )

    @staticmethod
    def _redact_unverified_mentions(text: str, evidence: list[RetrievedChunk]) -> tuple[str, list[str]]:
        pages = {c.source.page for c in evidence if c.source.type == "pdf"}
        slides = {c.source.slide for c in evidence if c.source.type == "slide"}
        stamps: set[str] = set()
        files = {c.source.file_name.casefold() for c in evidence}
        for c in evidence:
            if c.source.type == "video":
                stamps.add(c.source.timestamp_start)
                if c.source.timestamp_end:
                    stamps.add(c.source.timestamp_end)
        redacted: list[str] = []

        def _sub(pattern: re.Pattern[str], ok: Any) -> None:
            nonlocal text

            def repl(m: re.Match[str]) -> str:
                if ok(m):
                    return m.group(0)
                redacted.append(m.group(0))
                return REDACTION

            text = pattern.sub(repl, text)

        _sub(_PAGE_RE, lambda m: int(m.group(1)) in pages)
        _sub(_SLIDE_RE, lambda m: int(m.group(1)) in slides)
        _sub(_TIMESTAMP_RE, lambda m: format_timestamp(parse_timestamp(m.group(0))) in stamps)
        _sub(_FILENAME_RE, lambda m: m.group(0).casefold() in files)
        return text, redacted
