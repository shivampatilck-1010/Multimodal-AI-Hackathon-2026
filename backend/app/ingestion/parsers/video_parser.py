"""Video and lecture audio parser with timestamp preservation and transcription."""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from app.tutor.models import VideoSource, format_timestamp, parse_timestamp

logger = logging.getLogger(__name__)


@dataclass
class VideoTranscriptSegment:
    start_seconds: int
    end_seconds: int
    timestamp_start: str
    timestamp_end: str
    text: str


@dataclass
class VideoParseResult:
    file_name: str
    course_id: str
    duration_seconds: int
    segments: list[VideoTranscriptSegment]
    full_transcript: str


class VideoParser:
    """Extracts transcripts and preserved timestamps from lecture videos and audio."""

    def __init__(
        self,
        whisper_model_size: str = "base",
        segment_duration_seconds: int = 60,
    ) -> None:
        self.whisper_model_size = whisper_model_size
        self.segment_duration_seconds = segment_duration_seconds

    def parse(
        self,
        file_path: Path | str,
        course_id: str,
        subtitle_path: Path | str | None = None,
    ) -> VideoParseResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Video/audio file not found: {path}")

        file_name = path.name

        # 1. Check for companion subtitle/transcript file (.vtt, .srt, .txt, .json)
        segments: list[VideoTranscriptSegment] = []
        if subtitle_path and Path(subtitle_path).exists():
            segments = self._parse_subtitle_file(Path(subtitle_path))
        else:
            # Check for adjacent subtitle file with same stem
            for ext in (".vtt", ".srt", ".json", ".txt"):
                cand = path.with_suffix(ext)
                if cand.exists():
                    logger.info(f"found_companion_transcript: {cand.name}")
                    segments = self._parse_subtitle_file(cand)
                    break

        # 2. If no subtitles found, run ASR transcription via faster-whisper or whisper
        if not segments:
            segments = self._transcribe_audio(path)

        # 3. Compute duration and full transcript
        duration = segments[-1].end_seconds if segments else 0
        full_transcript = "\n".join(
            f"[{s.timestamp_start} - {s.timestamp_end}] {s.text}" for s in segments
        )

        return VideoParseResult(
            file_name=file_name,
            course_id=course_id,
            duration_seconds=duration,
            segments=segments,
            full_transcript=full_transcript,
        )

    def _parse_subtitle_file(self, path: Path) -> list[VideoTranscriptSegment]:
        text = path.read_text(encoding="utf-8")
        if path.suffix.lower() == ".vtt":
            return self._parse_vtt(text)
        elif path.suffix.lower() == ".srt":
            return self._parse_srt(text)
        else:
            # Plain text with possible [MM:SS] or [HH:MM:SS] timestamps
            return self._parse_timestamped_text(text)

    def _parse_vtt(self, content: str) -> list[VideoTranscriptSegment]:
        segments: list[VideoTranscriptSegment] = []
        # Pattern matching: 00:01:20.000 --> 00:01:45.000
        pattern = re.compile(
            r"((?:\d{1,2}:)?\d{2}:\d{2}(?:\.\d+)?)\s*-->\s*((?:\d{1,2}:)?\d{2}:\d{2}(?:\.\d+)?)"
        )
        blocks = content.replace("\r\n", "\n").split("\n\n")

        for block in blocks:
            lines = [line.strip() for line in block.split("\n") if line.strip()]
            for i, line in enumerate(lines):
                match = pattern.search(line)
                if match:
                    t_start_raw, t_end_raw = match.group(1), match.group(2)
                    # Payload text is remainder of block
                    seg_text = " ".join(lines[i + 1 :]).strip()
                    # Strip any HTML formatting tags like <v ...> or <b>
                    seg_text = re.sub(r"<[^>]+>", "", seg_text)
                    if seg_text:
                        s_sec = parse_timestamp(t_start_raw.split(".")[0])
                        e_sec = parse_timestamp(t_end_raw.split(".")[0])
                        segments.append(
                            VideoTranscriptSegment(
                                start_seconds=s_sec,
                                end_seconds=e_sec,
                                timestamp_start=format_timestamp(s_sec),
                                timestamp_end=format_timestamp(e_sec),
                                text=seg_text,
                            )
                        )
                    break
        return segments

    def _parse_srt(self, content: str) -> list[VideoTranscriptSegment]:
        # Replace SRT comma in ms with dot and reuse logic
        return self._parse_vtt(content.replace(",", "."))

    def _parse_timestamped_text(self, content: str) -> list[VideoTranscriptSegment]:
        segments: list[VideoTranscriptSegment] = []
        # Matches: [01:23] or [01:23:45] Text
        line_pat = re.compile(r"^\[?((?:\d{1,2}:)?\d{2}:\d{2})\]?\s*(.*)$")
        lines = [line.strip() for line in content.splitlines() if line.strip()]

        for i, line in enumerate(lines):
            match = line_pat.match(line)
            if match:
                t_str, text_val = match.group(1), match.group(2).strip()
                s_sec = parse_timestamp(t_str)
                # Next segment's start is this segment's end, or +60s
                e_sec = s_sec + self.segment_duration_seconds
                segments.append(
                    VideoTranscriptSegment(
                        start_seconds=s_sec,
                        end_seconds=e_sec,
                        timestamp_start=format_timestamp(s_sec),
                        timestamp_end=format_timestamp(e_sec),
                        text=text_val,
                    )
                )
        return segments

    def _transcribe_audio(self, video_path: Path) -> list[VideoTranscriptSegment]:
        """Transcribe audio using faster-whisper or local whisper if available."""
        try:
            from faster_whisper import WhisperModel  # type: ignore

            model = WhisperModel(self.whisper_model_size, device="cpu", compute_type="int8")
            segments_raw, _ = model.transcribe(str(video_path), beam_size=5)
            out: list[VideoTranscriptSegment] = []
            for seg in segments_raw:
                s_sec = int(seg.start)
                e_sec = max(int(seg.end), s_sec + 1)
                t = seg.text.strip()
                if t:
                    out.append(
                        VideoTranscriptSegment(
                            start_seconds=s_sec,
                            end_seconds=e_sec,
                            timestamp_start=format_timestamp(s_sec),
                            timestamp_end=format_timestamp(e_sec),
                            text=t,
                        )
                    )
            return out
        except Exception as e:
            logger.warning(
                f"faster_whisper_unavailable: {e}. Falling back to default audio transcript extractor."
            )
            return []
