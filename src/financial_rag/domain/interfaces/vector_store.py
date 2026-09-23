"""Architectural contract for vector database interactions."""

from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.models import DocumentChunk, RetrievalResult


@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Contract for vector databases (Qdrant, Pinecone, pgvector)."""

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> bool:
        """Store or update document chunk vectors with metadata payloads."""
        ...

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
        score_threshold: float | None = None,
        tenant_id: str | None = None,
    ) -> list[RetrievalResult]:
        """Perform similarity search and return ranked results."""
        ...

    async def initialize_collection(
        self, dimension: int, collection_name: str | None = None
    ) -> bool:
        """Initialize or verify vector collection with specified dimension."""
        ...

    async def delete_by_document_id(self, document_id: str, tenant_id: str | None = None) -> bool:
        """Remove all indexed chunks belonging to a document."""
        ...

    async def health_check(self) -> bool:
        """Verify vector store connection health."""
        ...
