"""Architectural contract for relational data persistence."""

from typing import Protocol, runtime_checkable

from financial_rag.common.types import DocumentId, JobId, VersionId
from financial_rag.domain.entities.models import (
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentVersion,
    IngestionJob,
)


@runtime_checkable
class DocumentRepositoryProtocol(Protocol):
    """Repository contract for Document entities."""

    async def save(self, document: Document) -> Document:
        """Persist or update document metadata."""
        ...

    async def get_by_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> Document | None:
        """Retrieve document by ID."""
        ...

    async def get_by_hash(
        self, file_hash_sha256: str, tenant_id: str | None = None
    ) -> Document | None:
        """Retrieve document by binary content SHA-256 hash."""
        ...

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        ticker_symbol: str | None = None,
        tenant_id: str | None = None,
    ) -> list[Document]:
        """List documents with optional filtering."""
        ...

    async def delete(self, document_id: DocumentId, tenant_id: str | None = None) -> bool:
        """Delete document record."""
        ...

    async def health_check(self) -> bool:
        """Verify relational database connection health."""
        ...


@runtime_checkable
class DocumentVersionRepositoryProtocol(Protocol):
    """Repository contract for DocumentVersion entities."""

    async def save(self, version: DocumentVersion) -> DocumentVersion:
        """Persist or update document version."""
        ...

    async def get_by_id(
        self, version_id: VersionId, tenant_id: str | None = None
    ) -> DocumentVersion | None:
        """Retrieve version by ID."""
        ...

    async def get_by_hash(
        self, file_hash_sha256: str, tenant_id: str | None = None
    ) -> DocumentVersion | None:
        """Retrieve version by file hash."""
        ...

    async def get_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> list[DocumentVersion]:
        """Retrieve all versions of a document ordered by version number."""
        ...

    async def get_latest_version(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> DocumentVersion | None:
        """Retrieve the highest version number for a document."""
        ...


@runtime_checkable
class DocumentPageRepositoryProtocol(Protocol):
    """Repository contract for DocumentPage storage."""

    async def save_batch(self, pages: list[DocumentPage]) -> int:
        """Bulk persist document pages."""
        ...

    async def get_by_version_id(
        self, version_id: VersionId, tenant_id: str | None = None
    ) -> list[DocumentPage]:
        """Retrieve all pages belonging to a document version."""
        ...

    async def get_by_document_and_page(
        self, document_id: DocumentId, page_number: int, tenant_id: str | None = None
    ) -> DocumentPage | None:
        """Retrieve single page by document ID and page number."""
        ...


@runtime_checkable
class IngestionJobRepositoryProtocol(Protocol):
    """Repository contract for tracking asynchronous ingestion jobs."""

    async def save(self, job: IngestionJob) -> IngestionJob:
        """Persist or update ingestion job state."""
        ...

    async def get_by_id(self, job_id: JobId, tenant_id: str | None = None) -> IngestionJob | None:
        """Retrieve ingestion job status by ID."""
        ...

    async def get_latest_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> IngestionJob | None:
        """Retrieve the latest ingestion job for a document."""
        ...

    async def list_jobs(
        self, limit: int = 50, offset: int = 0, tenant_id: str | None = None
    ) -> list[IngestionJob]:
        """List ingestion jobs ordered by creation timestamp."""
        ...

    async def get_pending_jobs(self, limit: int = 10) -> list[IngestionJob]:
        """Retrieve pending ingestion jobs ready for asynchronous processing."""
        ...


@runtime_checkable
class ChunkRepositoryProtocol(Protocol):
    """Repository contract for DocumentChunk storage."""

    async def save(self, chunk: DocumentChunk) -> DocumentChunk:
        """Persist a single chunk."""
        ...

    async def save_batch(self, chunks: list[DocumentChunk]) -> int:
        """Bulk persist chunks."""
        ...

    async def get_by_id(self, chunk_id: str, tenant_id: str | None = None) -> DocumentChunk | None:
        """Retrieve chunk by its ID."""
        ...

    async def get_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> list[DocumentChunk]:
        """Retrieve all chunks belonging to a document."""
        ...

    async def get_by_version_id(
        self, version_id: VersionId, tenant_id: str | None = None
    ) -> list[DocumentChunk]:
        """Retrieve all chunks belonging to a specific document version."""
        ...

    async def delete_by_document_id(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> int:
        """Delete all chunks for a document."""
        ...


# Alias for consistency
DocumentChunkRepositoryProtocol = ChunkRepositoryProtocol
