"""Deterministic mock OCR adapter for unit testing and offline environments."""

from uuid import uuid4

from financial_rag.common.types import BlockType, ExtractionMethod
from financial_rag.domain.entities.models import LayoutBlock
from financial_rag.domain.entities.value_objects import BoundingBox
from financial_rag.domain.interfaces.ocr import OCRAdapterProtocol, OCRResult
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.ocr.mock")


class MockOCRAdapter(OCRAdapterProtocol):
    """Deterministic OCR adapter that generates predictable text/blocks without external engine."""

    def __init__(self, default_text: str | None = None) -> None:
        self._default_text = default_text

    async def ocr_page(self, image_bytes: bytes, page_number: int = 1) -> OCRResult:
        """Produce deterministic mock OCR result."""
        text = (
            self._default_text
            or f"[OCR Scanned Page {page_number}] Extracted financial disclosure text."
        )
        block = LayoutBlock(
            id=str(uuid4()),
            page_number=page_number,
            block_type=BlockType.TEXT,
            content=text,
            reading_order=1,
            bounding_box=BoundingBox(
                x0=50.0, y0=50.0, x1=500.0, y1=700.0, page_width=595.0, page_height=842.0
            ),
            confidence=0.98,
            source_method=ExtractionMethod.OCR,
        )
        logger.info(f"MockOCRAdapter extracted text for page {page_number} ({len(text)} chars)")
        return OCRResult(
            text=text,
            blocks=[block],
            confidence=0.98,
            metadata={"engine": "mock_ocr", "page_number": page_number},
        )

    async def health_check(self) -> bool:
        return True
