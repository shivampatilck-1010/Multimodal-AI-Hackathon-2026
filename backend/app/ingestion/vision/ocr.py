"""OCR utility for scanned pages and image-heavy slides."""

from __future__ import annotations

import logging
from PIL import Image

logger = logging.getLogger(__name__)


class OcrEngine:
    """Performs OCR on images when text extraction is empty or below threshold."""

    def __init__(self) -> None:
        self._tesseract_available = False
        try:
            import pytesseract  # type: ignore

            pytesseract.get_tesseract_version()
            self._tesseract_available = True
        except Exception:
            self._tesseract_available = False

    def extract_text(self, image: Image.Image) -> str:
        """Extract text from a PIL image using pytesseract if available."""
        if not self._tesseract_available:
            return ""
        try:
            import pytesseract  # type: ignore

            return pytesseract.image_to_string(image).strip()
        except Exception as e:
            logger.warning(f"ocr_extraction_failed: {e}")
            return ""
