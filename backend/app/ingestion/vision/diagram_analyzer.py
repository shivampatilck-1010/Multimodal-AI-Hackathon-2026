"""Diagram and figure understanding engine.

Extracts visual knowledge, generates explanations, and links diagrams to concepts.
"""

from __future__ import annotations

import io
import json
import logging
from pathlib import Path

from PIL import Image

from app.kb.models import FigureUnit

logger = logging.getLogger(__name__)

DIAGRAM_PROMPT = """You are an expert academic diagram analyst for an educational knowledge base.
Analyze this academic figure or diagram from course materials.

Surrounding context from the document:
{context}

Return a valid JSON object with the following schema:
{{
  "caption": "A concise, descriptive title for this diagram (10-15 words max)",
  "explanation": "A clear, comprehensive explanation of what this diagram illustrates, including key processes, components, labeled elements, and educational takeaways (2-4 sentences)",
  "concepts": ["Concept 1", "Concept 2", "Concept 3"]
}}
Only return the valid JSON object, no markdown code fence.
"""


class DiagramAnalyzer:
    """Analyzes figures and diagrams to produce semantic captions and explanations."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-3.8-flash") -> None:
        self.api_key = api_key
        self.model = model
        self._client = None
        if api_key:
            try:
                from google import genai

                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                logger.warning(f"could_not_initialize_genai_client: {e}")

    def analyze_figure(
        self,
        figure: FigureUnit,
        image_path: Path,
        context_text: str = "",
    ) -> FigureUnit:
        """Enrich a FigureUnit with caption, explanation, and associated concepts."""
        if not image_path.exists():
            logger.warning(f"image_file_not_found: {image_path}")
            return figure

        # 1. Try Gemini Vision if client available
        if self._client:
            try:
                from google.genai import types

                with Image.open(image_path) as img:
                    # Convert to RGB if needed (e.g. RGBA or P mode)
                    if img.mode not in ("RGB", "L"):
                        img = img.convert("RGB")
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85)
                    img_bytes = buf.getvalue()

                prompt = DIAGRAM_PROMPT.format(context=context_text[:1500])
                response = self._client.models.generate_content(
                    model=self.model,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                        prompt,
                    ],
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                parsed = json.loads(text.strip())

                figure.caption = parsed.get("caption", figure.caption)
                figure.explanation = parsed.get("explanation", "")
                figure.associated_concepts = parsed.get("concepts", [])
                logger.info("figure_analyzed_with_gemini", extra={"figure_id": figure.id})
                return figure
            except Exception as e:
                logger.warning(f"gemini_diagram_analysis_failed_for_{figure.id}: {e}")

        # 2. Offline deterministic fallback
        figure.caption = figure.caption or f"Diagram from {figure.source.location_label()}"
        first_sentence = context_text.split(".")[0] if context_text else ""
        figure.explanation = (
            f"Visual figure corresponding to {figure.source.location_label()}. "
            f"Context: {first_sentence.strip()}."
        )
        return figure
