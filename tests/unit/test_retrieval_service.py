"""Unit tests for RetrievalService orchestrator, latency tracking, and fallback handling."""

import pytest

from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.config.settings import RetrievalSettings
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import (
    RetrievalCandidate,
    RetrievalQuery,
    RetrievalSource,
)
from financial_rag.domain.exceptions import RetrievalError
from financial_rag.infrastructure.retrieval.deduplicator import CandidateDeduplicator
from financial_rag.infrastructure.retrieval.evidence_selector import EvidenceSelector
from financial_rag.infrastructure.retrieval.evidence_validator import EvidenceValidator
from financial_rag.infrastructure.retrieval.fusion import ReciprocalRankFusion
from financial_rag.infrastructure.retrieval.query_analyzer import FinancialQueryAnalyzer
from financial_rag.infrastructure.retrieval.reranker import MockReranker


class WorkingDenseRetriever:
    async def retrieve(
        self, query: RetrievalQuery, top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        chunk = DocumentChunk(
            id="dense-chunk-1",
            document_id="doc-1",
            page_number=1,
            chunk_index=0,
            content="Apple revenue was $391B.",
        )
        return [RetrievalCandidate(chunk=chunk, dense_score=0.9, sources=[RetrievalSource.DENSE])]

    async def health_check(self) -> bool:
        return True


class WorkingSparseRetriever:
    async def retrieve(
        self, query: RetrievalQuery, top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        chunk = DocumentChunk(
            id="sparse-chunk-1",
            document_id="doc-1",
            page_number=2,
            chunk_index=1,
            content="Services revenue rose 13%.",
        )
        return [
            RetrievalCandidate(chunk=chunk, sparse_score=0.85, sources=[RetrievalSource.SPARSE])
        ]

    async def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        return len(chunks)

    async def delete_by_document_id(self, document_id: str) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


class FailingDenseRetriever:
    async def retrieve(
        self, query: RetrievalQuery, top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        raise ConnectionError("Qdrant cluster unavailable")

    async def health_check(self) -> bool:
        return False


class FailingSparseRetriever:
    async def retrieve(
        self, query: RetrievalQuery, top_k: int | None = None
    ) -> list[RetrievalCandidate]:
        raise RuntimeError("BM25 index corrupted")

    async def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        return 0

    async def delete_by_document_id(self, document_id: str) -> bool:
        return False

    async def health_check(self) -> bool:
        return False


@pytest.mark.asyncio
async def test_retrieval_service_happy_path() -> None:
    service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=WorkingDenseRetriever(),
        sparse_retriever=WorkingSparseRetriever(),
        fusion_strategy=ReciprocalRankFusion(),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
    )

    evidence_set = await service.search(raw_query="What was Apple revenue in 2024?", top_k=2)

    assert evidence_set.evidence_count == 2
    assert "query_analysis" in evidence_set.execution_stages
    assert "dense_retrieval" in evidence_set.execution_stages
    assert "sparse_retrieval" in evidence_set.execution_stages
    assert "candidate_fusion" in evidence_set.execution_stages
    assert "reranking" in evidence_set.execution_stages
    assert "evidence_selection" in evidence_set.execution_stages
    assert "validation" in evidence_set.execution_stages
    assert evidence_set.fallback_occurred is False
    assert "total" in evidence_set.timing_ms


@pytest.mark.asyncio
async def test_retrieval_service_dense_fallback() -> None:
    # Dense fails -> falls back gracefully to sparse only
    service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=FailingDenseRetriever(),
        sparse_retriever=WorkingSparseRetriever(),
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
    assert evidence_set.items[0].chunk_id == "sparse-chunk-1"


@pytest.mark.asyncio
async def test_retrieval_service_sparse_fallback() -> None:
    # Sparse fails -> falls back gracefully to dense only
    service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=WorkingDenseRetriever(),
        sparse_retriever=FailingSparseRetriever(),
        fusion_strategy=ReciprocalRankFusion(),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
        retrieval_settings=RetrievalSettings(enable_dense_fallback=True),
    )

    evidence_set = await service.search(raw_query="What was revenue?", top_k=2)
    assert evidence_set.evidence_count == 1
    assert evidence_set.fallback_occurred is True
    assert "Sparse retrieval unavailable" in str(evidence_set.fallback_reason)
    assert evidence_set.items[0].chunk_id == "dense-chunk-1"


@pytest.mark.asyncio
async def test_retrieval_service_dual_failure() -> None:
    # Both fail -> raises RetrievalError
    service = RetrievalService(
        query_analyzer=FinancialQueryAnalyzer(),
        dense_retriever=FailingDenseRetriever(),
        sparse_retriever=FailingSparseRetriever(),
        fusion_strategy=ReciprocalRankFusion(),
        deduplicator=CandidateDeduplicator(),
        reranker=MockReranker(),
        evidence_selector=EvidenceSelector(),
        evidence_validator=EvidenceValidator(),
    )

    with pytest.raises(RetrievalError, match="Both dense and sparse retrieval systems failed"):
        await service.search(raw_query="What was revenue?")
