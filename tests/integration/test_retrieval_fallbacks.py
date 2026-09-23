"""Integration tests for retrieval failure handling and graceful fallbacks."""

import pytest

from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.config.settings import RetrievalSettings
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalQuery,
    RetrievalSource,
)
from financial_rag.infrastructure.retrieval import (
    CandidateDeduplicator,
    EvidenceSelector,
    EvidenceValidator,
    FinancialQueryAnalyzer,
    MockReranker,
    ReciprocalRankFusion,
)


class CrashingDenseRetriever:
    async def retrieve(
        self, query: RetrievalQuery, top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        raise TimeoutError("Qdrant query timed out after 10000ms")

    async def health_check(self) -> bool:
        return False


class CrashingReranker:
    async def rerank(
        self, query: RetrievalQuery, candidates: list[RetrievalCandidate], top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        raise RuntimeError("Reranker GPU Out Of Memory")

    async def health_check(self) -> bool:
        return False


class StubSparseRetriever:
    async def retrieve(
        self, query: RetrievalQuery, top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        chunk = DocumentChunk(
            id="c-sparse-fallback",
            document_id="doc-sparse",
            page_number=1,
            chunk_index=0,
            content="Fallback content retrieved via BM25.",
        )
        return [
            RetrievalCandidate(chunk=chunk, sparse_score=0.82, sources=[RetrievalSource.SPARSE])
        ]

    async def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        return len(chunks)

    async def delete_by_document_id(self, document_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


@pytest.mark.asyncio
async def test_dense_failure_triggers_sparse_fallback() -> None:
    service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=CrashingDenseRetriever(),
        sparse_retriever=StubSparseRetriever(),
        fusion_strategy=ReciprocalRankFusion(),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
        retrieval_settings=RetrievalSettings(enable_sparse_fallback=True),
    )

    evidence_set = await service.search(raw_query="What was revenue?", top_k=2)

    assert evidence_set.evidence_count == 1
    assert evidence_set.fallback_occurred is True
    assert "Dense retrieval unavailable" in str(evidence_set.fallback_reason)
    assert evidence_set.retrieval_strategy.startswith("sparse_only_fallback")
    assert "sparse_retrieval" in evidence_set.execution_stages
    assert "dense_retrieval" not in evidence_set.execution_stages


@pytest.mark.asyncio
async def test_reranker_failure_triggers_fused_fallback() -> None:
    service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=CrashingDenseRetriever(),
        sparse_retriever=StubSparseRetriever(),
        fusion_strategy=ReciprocalRankFusion(),
        deduplicator=CandidateDeduplicator(),
        reranker=CrashingReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
        retrieval_settings=RetrievalSettings(enable_sparse_fallback=True),
    )

    evidence_set = await service.search(raw_query="What was revenue?", top_k=2, use_reranker=True)

    assert evidence_set.evidence_count == 1
    assert evidence_set.fallback_occurred is True
    assert "Reranker failed" in str(evidence_set.fallback_reason)
    assert "reranking" not in evidence_set.execution_stages
