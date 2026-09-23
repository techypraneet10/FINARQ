"""Unit tests for the complete ReasoningService orchestrator workflow."""

from unittest.mock import AsyncMock

import pytest

from financial_rag.application.reasoning.service import ReasoningService
from financial_rag.domain.entities.reasoning import AnswerabilityStatus
from financial_rag.domain.entities.retrieval import (
    EvidenceSet,
    FinancialSignals,
    QueryType,
    RetrievalFilter,
    RetrievalQuery,
)
from financial_rag.domain.interfaces.retrieval import RetrievalServiceProtocol
from tests.fixtures.financial_reasoning_fixtures import (
    make_sample_apple_narrative_evidence,
    make_sample_apple_table_evidence,
)


@pytest.mark.asyncio
async def test_reasoning_service_end_to_end() -> None:
    table_ev = make_sample_apple_table_evidence()
    narrative_ev = make_sample_apple_narrative_evidence()

    mock_query = RetrievalQuery(
        raw_query="What was Apple's total revenue in 2024?",
        normalized_query="apple total revenue 2024",
        query_type=QueryType.FACTUAL,
        signals=FinancialSignals(tickers=["AAPL"], metrics=["Revenue"], fiscal_years=[2024]),
        filters=RetrievalFilter(),
    )
    mock_evidence_set = EvidenceSet(
        query_id=mock_query.id,
        query=mock_query,
        items=[table_ev, narrative_ev],
        total_candidates=2,
        retrieval_strategy="hybrid_dense_sparse_rrf_rerank",
        execution_stages=["dense", "sparse", "fusion", "rerank", "selection"],
        timing_ms={"total_ms": 15.0},
    )

    mock_retrieval_service = AsyncMock(spec=RetrievalServiceProtocol)
    mock_retrieval_service.search.return_value = mock_evidence_set

    service = ReasoningService(retrieval_service=mock_retrieval_service)

    package = await service.reason(raw_query="What was Apple's total revenue in 2024?")

    assert package is not None
    assert package.answerability == AnswerabilityStatus.ANSWERABLE
    assert len(package.facts) >= 1
    assert len(package.claims) >= 1
    assert len(package.citations) >= 1
    assert all(c.verified for c in package.citations)
    assert package.grounding_validation is not None
    assert package.grounding_validation.validation_passed
    assert "total_ms" in package.execution_time_ms
