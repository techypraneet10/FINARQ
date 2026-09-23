"""Architectural contract for PDF parsing and classification."""

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from financial_rag.common.types import PDFType
from financial_rag.domain.entities.models import DocumentPage


@dataclass
class ParsedDocument:
    """Container holding extracted document pages and classification details."""

    pages: list[DocumentPage]
    pdf_type: PDFType
    total_pages: int
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class PDFClassifierProtocol(Protocol):
    """Contract for determining whether a PDF is native text, scanned image, or hybrid."""

    def classify(self, content: bytes) -> PDFType:
        """Classify PDF by layout characteristics."""
        ...


@runtime_checkable
class PDFParserProtocol(Protocol):
    """Contract for layout-aware PDF text, block, and table parsing."""

    async def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        """Parse raw PDF binary and return structured document pages with layout blocks."""
        ...
