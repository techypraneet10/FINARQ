"""Architectural contract for Optical Character Recognition (OCR)."""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.models import LayoutBlock


@dataclass
class OCRResult:
    """Extracted text and structural layout blocks produced by OCR."""

    text: str
    blocks: list[LayoutBlock] = field(default_factory=list)
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class OCRAdapterProtocol(Protocol):
    """Contract for replaceable OCR engines (Tesseract, EasyOCR, Mock)."""

    async def ocr_page(self, image_bytes: bytes, page_number: int = 1) -> OCRResult:
        """Perform OCR on a single rendered page image."""
        ...

    async def health_check(self) -> bool:
        """Verify OCR engine availability."""
        ...
