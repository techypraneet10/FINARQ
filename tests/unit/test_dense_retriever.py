"""Unit tests for Qdrant dense vector retriever adapter."""

from typing import Any

import pytest

from financial_rag.domain.entities.models import DocumentChunk, RetrievalResult
from financial_rag.domain.entities.retrieval import RetrievalFilter, RetrievalQuery, RetrievalSource
from financial_rag.domain.exceptions import IncompatibleEmbeddingError
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.retrieval.dense_retriever import QdrantDenseRetriever


class FakeVectorStore:
    def __init__(self) -> None:
        self.searched_with_filters: dict[str, Any] | None = None
        self.query_vector: list[float] | None = None

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 10,
        filters: dict | None = None,
        score_threshold: float | None = None,
    ) -> list[RetrievalResult]:
        self.query_vector = query_vector
        self.searched_with_filters = filters

        chunk = DocumentChunk(
            id="fake-chunk-1",
            document_id="doc-fake",
            document_version_id="ver-fake",
            page_number=5,
            chunk_index=0,
            content="Fake financial content for vector match.",
            section_path="Item 8 > Operations",
        )
        return [RetrievalResult(chunk=chunk, score=0.88, retrieval_method="dense_vector")]

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_qdrant_dense_retriever_basic() -> None:
    embedder = MockEmbeddingProvider(dimension=1536)
    vector_store = FakeVectorStore()
    retriever = QdrantDenseRetriever(
        embedding_provider=embedder,
        vector_store=vector_store,  # type: ignore[arg-type]
        expected_dimension=1536,
    )

    query = RetrievalQuery(
        raw_query="What was revenue?",
        normalized_query="What was revenue?",
        filters=RetrievalFilter(document_ids=["doc-fake"], ticker_symbols=["AAPL"]),
    )

    candidates = await retriever.retrieve(query, top_k=5)
    assert len(candidates) == 1
    assert candidates[0].chunk.id == "fake-chunk-1"
    assert candidates[0].dense_score == 0.88
    assert candidates[0].dense_rank == 1
    assert candidates[0].sources == [RetrievalSource.DENSE]
    assert candidates[0].provenance is not None
    assert candidates[0].provenance.document_id == "doc-fake"

    # Verify filter translation
    assert vector_store.searched_with_filters == {
        "tenant_id": "default_tenant",
        "document_id": "doc-fake",
        "ticker_symbol": "AAPL",
    }
    assert await retriever.health_check() is True


@pytest.mark.asyncio
async def test_incompatible_embedding_dimension() -> None:
    embedder = MockEmbeddingProvider(dimension=768)
    vector_store = FakeVectorStore()
    retriever = QdrantDenseRetriever(
        embedding_provider=embedder,
        vector_store=vector_store,  # type: ignore[arg-type]
        expected_dimension=1536,  # Mismatched expected collection dimension
    )

    query = RetrievalQuery(raw_query="test", normalized_query="test")
    with pytest.raises(IncompatibleEmbeddingError, match="Vector dimension mismatch"):
        await retriever.retrieve(query)
