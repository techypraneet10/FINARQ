"""Architectural contract for document text normalization and financial structure detection."""

from typing import Protocol, runtime_checkable

from financial_rag.common.types import DocumentType
from financial_rag.domain.entities.models import DocumentPage


@runtime_checkable
class DocumentNormalizerProtocol(Protocol):
    """Contract for lossless text and layout normalization."""

    def normalize(self, pages: list[DocumentPage]) -> list[DocumentPage]:
        """Apply Unicode normalization, whitespace cleanup, and financial artifact repair."""
        ...


@runtime_checkable
class StructureDetectorProtocol(Protocol):
    """Contract for SEC Item and financial statement structure detection."""

    def detect_structure(
        self, pages: list[DocumentPage], document_type: DocumentType = DocumentType.OTHER
    ) -> list[DocumentPage]:
        """Detect section headers, SEC 10-K/10-Q items, and financial statement blocks."""
        ...
