"""Semantic multimodal chunker with strict source provenance preservation."""

from __future__ import annotations

import logging
import re
from typing import Any

from app.tutor.models import (
    ContentUnit,
    PdfSource,
    SlideSource,
    VideoSource,
    format_timestamp,
)
from app.ingestion.parsers.pdf_parser import PdfParseResult
from app.ingestion.parsers.ppt_parser import PptParseResult
from app.ingestion.parsers.video_parser import VideoParseResult, VideoTranscriptSegment

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Chunks multimodal materials into ContentUnits respecting natural boundaries."""

    def __init__(
        self,
        max_chunk_chars: int = 1500,
        min_chunk_chars: int = 40,
        video_target_duration_seconds: int = 60,
    ) -> None:
        self.max_chunk_chars = max_chunk_chars
        self.min_chunk_chars = min_chunk_chars
        self.video_target_duration_seconds = video_target_duration_seconds

    # ------------------------------------------------------------- PDF Chunking
    def chunk_pdf(self, parsed: PdfParseResult) -> list[ContentUnit]:
        units: list[ContentUnit] = []
        stem = re.sub(r"[^A-Za-z0-9_]+", "_", Path_stem(parsed.file_name))

        for page in parsed.pages:
            text = page.text.strip()
            page_figs = [f.id for f in page.figures]

            if not text and not page_figs:
                continue

            # If page text is within budget, keep page intact
            if len(text) <= self.max_chunk_chars and text:
                chunk_id = f"unit_{stem}_p{page.page_number}_01"
                units.append(
                    ContentUnit(
                        id=chunk_id,
                        course_id=parsed.course_id,
                        text=text,
                        source=PdfSource(
                            type="pdf",
                            file_name=parsed.file_name,
                            page=page.page_number,
                        ),
                        metadata={
                            "page": page.page_number,
                            "figure_ids": page_figs,
                        },
                    )
                )
            elif text:
                # Split long page into coherent paragraph chunks
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                current_block: list[str] = []
                current_len = 0
                part_idx = 1

                for p in paragraphs:
                    if current_len + len(p) > self.max_chunk_chars and current_block:
                        chunk_text = "\n\n".join(current_block).strip()
                        if len(chunk_text) >= self.min_chunk_chars:
                            chunk_id = f"unit_{stem}_p{page.page_number}_{part_idx:02d}"
                            units.append(
                                ContentUnit(
                                    id=chunk_id,
                                    course_id=parsed.course_id,
                                    text=chunk_text,
                                    source=PdfSource(
                                        type="pdf",
                                        file_name=parsed.file_name,
                                        page=page.page_number,
                                    ),
                                    metadata={
                                        "page": page.page_number,
                                        "part": part_idx,
                                        "figure_ids": page_figs if part_idx == 1 else [],
                                    },
                                )
                            )
                            part_idx += 1
                        current_block = [p]
                        current_len = len(p)
                    else:
                        current_block.append(p)
                        current_len += len(p)

                if current_block:
                    chunk_text = "\n\n".join(current_block).strip()
                    if len(chunk_text) >= self.min_chunk_chars:
                        chunk_id = f"unit_{stem}_p{page.page_number}_{part_idx:02d}"
                        units.append(
                            ContentUnit(
                                id=chunk_id,
                                course_id=parsed.course_id,
                                text=chunk_text,
                                source=PdfSource(
                                    type="pdf",
                                    file_name=parsed.file_name,
                                    page=page.page_number,
                                ),
                                metadata={
                                    "page": page.page_number,
                                    "part": part_idx,
                                    "figure_ids": page_figs if part_idx == 1 else [],
                                },
                            )
                        )
            elif page_figs:
                # Page has no text but has figures: create placeholder unit for figures
                chunk_id = f"unit_{stem}_p{page.page_number}_fig"
                units.append(
                    ContentUnit(
                        id=chunk_id,
                        course_id=parsed.course_id,
                        text=f"[Diagrams on Page {page.page_number}]",
                        source=PdfSource(
                            type="pdf",
                            file_name=parsed.file_name,
                            page=page.page_number,
                        ),
                        metadata={"page": page.page_number, "figure_ids": page_figs},
                    )
                )

        return units

    # ------------------------------------------------------------- PPT Chunking
    def chunk_pptx(self, parsed: PptParseResult) -> list[ContentUnit]:
        units: list[ContentUnit] = []
        stem = re.sub(r"[^A-Za-z0-9_]+", "_", Path_stem(parsed.file_name))

        for slide in parsed.slides:
            text = slide.full_text.strip()
            slide_figs = [f.id for f in slide.figures]

            if not text and not slide_figs:
                continue

            chunk_id = f"unit_{stem}_s{slide.slide_number}"
            chunk_text = text if text else f"[Slide {slide.slide_number}: Visual Presentation]"

            units.append(
                ContentUnit(
                    id=chunk_id,
                    course_id=parsed.course_id,
                    text=chunk_text,
                    source=SlideSource(
                        type="slide",
                        file_name=parsed.file_name,
                        slide=slide.slide_number,
                    ),
                    metadata={
                        "slide": slide.slide_number,
                        "title": slide.title,
                        "has_notes": bool(slide.speaker_notes),
                        "figure_ids": slide_figs,
                    },
                )
            )

        return units

    # ----------------------------------------------------------- Video Chunking
    def chunk_video(self, parsed: VideoParseResult) -> list[ContentUnit]:
        units: list[ContentUnit] = []
        stem = re.sub(r"[^A-Za-z0-9_]+", "_", Path_stem(parsed.file_name))

        if not parsed.segments:
            return units

        # Merge short adjacent segments into coherent chunks around target duration
        cur_text_parts: list[str] = []
        cur_start = parsed.segments[0].start_seconds
        cur_end = parsed.segments[0].end_seconds
        chunk_idx = 1

        for seg in parsed.segments:
            duration = seg.end_seconds - cur_start
            if duration >= self.video_target_duration_seconds and cur_text_parts:
                combined_text = " ".join(cur_text_parts).strip()
                t_start = format_timestamp(cur_start)
                t_end = format_timestamp(cur_end)
                chunk_id = f"unit_{stem}_{cur_start:05d}_{chunk_idx:02d}"

                units.append(
                    ContentUnit(
                        id=chunk_id,
                        course_id=parsed.course_id,
                        text=combined_text,
                        source=VideoSource(
                            type="video",
                            file_name=parsed.file_name,
                            timestamp_start=t_start,
                            timestamp_end=t_end,
                        ),
                        metadata={
                            "start_seconds": cur_start,
                            "end_seconds": cur_end,
                            "chunk_index": chunk_idx,
                        },
                    )
                )
                chunk_idx += 1
                cur_text_parts = [seg.text]
                cur_start = seg.start_seconds
                cur_end = seg.end_seconds
            else:
                cur_text_parts.append(seg.text)
                cur_end = seg.end_seconds

        if cur_text_parts:
            combined_text = " ".join(cur_text_parts).strip()
            t_start = format_timestamp(cur_start)
            t_end = format_timestamp(cur_end)
            chunk_id = f"unit_{stem}_{cur_start:05d}_{chunk_idx:02d}"

            units.append(
                ContentUnit(
                    id=chunk_id,
                    course_id=parsed.course_id,
                    text=combined_text,
                    source=VideoSource(
                        type="video",
                        file_name=parsed.file_name,
                        timestamp_start=t_start,
                        timestamp_end=t_end,
                    ),
                    metadata={
                        "start_seconds": cur_start,
                        "end_seconds": cur_end,
                        "chunk_index": chunk_idx,
                    },
                )
            )

        return units


def Path_stem(filename: str) -> str:
    from pathlib import Path
    return Path(filename).stem
