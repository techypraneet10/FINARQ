"""Tesseract OCR adapter for scanned financial document pages."""

import asyncio
import io
from uuid import uuid4

from financial_rag.common.types import BlockType, ExtractionMethod
from financial_rag.domain.entities.models import LayoutBlock
from financial_rag.domain.entities.value_objects import BoundingBox
from financial_rag.domain.exceptions import OCRError
from financial_rag.domain.interfaces.ocr import OCRAdapterProtocol, OCRResult
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.ocr.tesseract")


class TesseractOCRAdapter(OCRAdapterProtocol):
    """OCR adapter leveraging Tesseract OCR engine."""

    def __init__(self, lang: str = "eng") -> None:
        self._lang = lang

    async def ocr_page(self, image_bytes: bytes, page_number: int = 1) -> OCRResult:
        """Execute Tesseract OCR on rendered page image."""
        try:
            import pytesseract
            from PIL import Image

            def _sync_ocr() -> OCRResult:
                image = Image.open(io.BytesIO(image_bytes))
                width, height = image.size

                extracted_text = pytesseract.image_to_string(image, lang=self._lang).strip()

                blocks: list[LayoutBlock] = []

                if extracted_text:
                    blocks.append(
                        LayoutBlock(
                            id=str(uuid4()),
                            page_number=page_number,
                            block_type=BlockType.TEXT,
                            content=extracted_text,
                            reading_order=1,
                            bounding_box=BoundingBox(
                                x0=0.0,
                                y0=0.0,
                                x1=float(width),
                                y1=float(height),
                                page_width=float(width),
                                page_height=float(height),
                            ),
                            confidence=0.95,
                            source_method=ExtractionMethod.OCR,
                        )
                    )

                return OCRResult(
                    text=extracted_text,
                    blocks=blocks,
                    confidence=0.95,
                    metadata={
                        "engine": "tesseract",
                        "lang": self._lang,
                        "page_number": page_number,
                    },
                )

            return await asyncio.to_thread(_sync_ocr)

        except ImportError:
            logger.warning(
                "pytesseract or PIL not installed, falling back to basic mock OCR response"
            )
            return OCRResult(
                text=f"[OCR Fallback Page {page_number}] Extracted text placeholder.",
                blocks=[],
                confidence=0.5,
                metadata={"engine": "tesseract_fallback_import_error"},
            )
        except Exception as ex:
            logger.warning(f"Tesseract OCR failed: {ex}")
            raise OCRError(
                message=f"Tesseract OCR failed for page {page_number}: {ex}",
                details={"page_number": page_number, "error": str(ex)},
            ) from ex

    async def health_check(self) -> bool:
        try:
            import pytesseract

            await asyncio.to_thread(pytesseract.get_tesseract_version)

            return True
        except Exception:
            return False
