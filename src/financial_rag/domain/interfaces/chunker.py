"""Architectural contract for structure-aware semantic chunking."""

from typing import Protocol, runtime_checkable

from financial_rag.common.types import DocumentId, VersionId
from financial_rag.domain.entities.models import DocumentChunk, DocumentPage


@runtime_checkable
class ChunkerProtocol(Protocol):
    """Contract for generating structure-aware chunks with full provenance."""

    def chunk_document(
        self,
        document_id: DocumentId,
        version_id: VersionId,
        pages: list[DocumentPage],
    ) -> list[DocumentChunk]:
        """Transform structured pages into validated chunks preserving section and table boundaries."""
        ...
