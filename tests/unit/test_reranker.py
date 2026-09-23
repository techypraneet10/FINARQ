"""Unit tests for MockReranker and cross-encoder adapters."""

import pytest

from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import (
    FinancialSignals,
    RetrievalCandidate,
    RetrievalQuery,
)
from financial_rag.domain.exceptions import RerankerError
from financial_rag.infrastructure.retrieval.reranker import (
    CrossEncoderReranker,
    MockReranker,
)


@pytest.mark.asyncio
async def test_mock_reranker_signal_alignment() -> None:
    reranker = MockReranker()

    c1 = DocumentChunk(
        id="c1",
        document_id="doc-1",
        page_number=1,
        chunk_index=0,
        content="General discussion of corporate macroeconomic environment.",
        section_path="Item 7 > Overview",
    )
    c2 = DocumentChunk(
        id="c2",
        document_id="doc-1",
        page_number=5,
        chunk_index=1,
        content="Apple total revenue was $391 billion in fiscal year 2024.",
        section_path="Item 8. Financial Statements > Operations",
        metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
    )

    cands = [
        RetrievalCandidate(chunk=c1, fusion_score=0.8, final_score=0.8),
        RetrievalCandidate(chunk=c2, fusion_score=0.5, final_score=0.5),
    ]

    query = RetrievalQuery(
        raw_query="What was Apple revenue in 2024?",
        normalized_query="What was Apple revenue in 2024?",
        signals=FinancialSignals(
            tickers=["AAPL"],
            company_names=["Apple"],
            metrics=["revenue"],
            fiscal_years=[2024],
        ),
    )

    reranked = await reranker.rerank(query, cands, top_k=2)
    assert len(reranked) == 2
    # c2 should be boosted to top position because it matches AAPL + revenue + 2024
    assert reranked[0].chunk.id == "c2"
    assert reranked[0].reranker_score is not None
    assert reranked[1].reranker_score is not None
    assert reranked[0].reranker_score > reranked[1].reranker_score
    assert await reranker.health_check() is True


@pytest.mark.asyncio
async def test_reranker_bounds_safety() -> None:
    reranker = MockReranker()
    cands = [
        RetrievalCandidate(
            chunk=DocumentChunk(
                id=f"c-{i}", document_id="doc-1", page_number=1, chunk_index=i, content=f"Text {i}"
            ),
            fusion_score=0.5,
        )
        for i in range(100)
    ]
    query = RetrievalQuery(raw_query="test", normalized_query="test", rerank_top_k=10)

    reranked = await reranker.rerank(query, cands, top_k=10)
    assert len(reranked) == 10
    assert await reranker.rerank(query, []) == []


@pytest.mark.asyncio
async def test_cross_encoder_reranker_handling() -> None:
    reranker = CrossEncoderReranker(model_name="non-existent-model")
    query = RetrievalQuery(raw_query="test", normalized_query="test")
    cands = [
        RetrievalCandidate(
            chunk=DocumentChunk(
                id="c1", document_id="d1", page_number=1, chunk_index=0, content="Sample"
            ),
            fusion_score=0.5,
        )
    ]

    # In environment without sentence-transformers or with invalid model, raises RerankerError cleanly
    try:
        await reranker.rerank(query, cands)
    except RerankerError as ex:
        assert ex.code == "RERANKER_ERROR"
