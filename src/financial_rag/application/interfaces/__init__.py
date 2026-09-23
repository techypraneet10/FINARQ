"""Application use cases and workflow orchestration contracts.

Actual financial RAG use case implementations (ingestion, processing, retrieval,
grounded reasoning, citation generation) are planned for Phase 1+.
"""

from typing import Protocol, runtime_checkable

from financial_rag.domain.entities.models import Answer, IngestionJob, Query


@runtime_checkable
class DocumentIngestionUseCaseProtocol(Protocol):
    """Contract for document ingestion and indexing orchestrator (Planned for Phase 1)."""

    async def execute(self, file_bytes: bytes, filename: str, metadata: dict) -> IngestionJob:
        """Trigger document ingestion pipeline."""
        ...


@runtime_checkable
class QueryAnsweringUseCaseProtocol(Protocol):
    """Contract for grounded financial question answering (Planned for Phase 2)."""

    async def execute(self, query: Query) -> Answer:
        """Execute retrieval, deterministic reasoning, and verifiable citation generation."""
        ...


__all__ = [
    "DocumentIngestionUseCaseProtocol",
    "QueryAnsweringUseCaseProtocol",
]
