"""PDF parser using PyMuPDF (fitz) with exact page numbering and figure extraction."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from app.tutor.models import PdfSource
from app.kb.models import BoundingBox, FigureUnit
from app.kb.media_store import MediaStore

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    page_number: int
    text: str
    figures: list[FigureUnit] = field(default_factory=list)
    needs_ocr: bool = False


@dataclass
class PdfParseResult:
    file_name: str
    course_id: str
    total_pages: int
    pages: list[ExtractedPage]
    figures: list[FigureUnit]


class PdfParser:
    """Extracts text and diagrams from textbooks and PDF lecture notes."""

    def __init__(
        self,
        media_store: MediaStore | None = None,
        min_image_dimension: int = 80,
        ocr_text_threshold: int = 40,
    ) -> None:
        self.media_store = media_store
        self.min_image_dimension = min_image_dimension
        self.ocr_text_threshold = ocr_text_threshold

    def parse(self, file_path: Path | str, course_id: str) -> PdfParseResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        file_name = path.name
        doc = fitz.open(str(path))
        extracted_pages: list[ExtractedPage] = []
        all_figures: list[FigureUnit] = []

        try:
            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_num = page_idx + 1  # 1-indexed

                # 1. Text extraction
                raw_text = page.get_text("text").strip()
                needs_ocr = len(raw_text) < self.ocr_text_threshold

                # 2. Extract embedded images & figures
                page_figures: list[FigureUnit] = []
                image_list = page.get_images(full=True)

                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image.get("image")
                    image_ext = base_image.get("ext", "png")

                    if not image_bytes:
                        continue

                    try:
                        pil_img = Image.open(io.BytesIO(image_bytes))
                        width, height = pil_img.size

                        # Filter out tiny icon / bullet glyphs
                        if (
                            width < self.min_image_dimension
                            or height < self.min_image_dimension
                        ):
                            continue

                        # Extract bounding box on page if possible
                        bbox_obj = None
                        rects = page.get_image_rects(xref)
                        if rects:
                            r = rects[0]
                            bbox_obj = BoundingBox(
                                x0=round(r.x0, 2),
                                y0=round(r.y0, 2),
                                x1=round(r.x1, 2),
                                y1=round(r.y1, 2),
                                width=round(r.width, 2),
                                height=round(r.height, 2),
                            )

                        fig_id = f"fig_{path.stem}_p{page_num}_{img_idx + 1}"
                        rel_path = ""
                        if self.media_store:
                            rel_path = self.media_store.save_image(
                                course_id=course_id,
                                figure_id=fig_id,
                                image=pil_img,
                                image_format=pil_img.format or "PNG",
                            )

                        figure = FigureUnit(
                            id=fig_id,
                            course_id=course_id,
                            source=PdfSource(
                                type="pdf",
                                file_name=file_name,
                                page=page_num,
                            ),
                            image_rel_path=rel_path,
                            caption="",
                            explanation="",
                            bounding_box=bbox_obj,
                            metadata={
                                "width": width,
                                "height": height,
                                "format": image_ext,
                            },
                        )
                        page_figures.append(figure)
                        all_figures.append(figure)

                    except Exception as e:
                        logger.warning(
                            f"failed_extracting_image_p{page_num}_img{img_idx}: {e}"
                        )

                page_data = ExtractedPage(
                    page_number=page_num,
                    text=raw_text,
                    figures=page_figures,
                    needs_ocr=needs_ocr,
                )
                extracted_pages.append(page_data)

            if self.media_store and all_figures:
                self.media_store.add_figures(all_figures)

            logger.info(
                "pdf_parsed_successfully",
                extra={
                    "file_name": file_name,
                    "pages": len(extracted_pages),
                    "figures": len(all_figures),
                },
            )

            return PdfParseResult(
                file_name=file_name,
                course_id=course_id,
                total_pages=len(doc),
                pages=extracted_pages,
                figures=all_figures,
            )
        finally:
            doc.close()
