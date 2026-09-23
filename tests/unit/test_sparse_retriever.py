"""Unit tests for Okapi BM25 sparse retriever and financial tokenization."""

import pytest

from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import RetrievalFilter, RetrievalQuery, RetrievalSource
from financial_rag.infrastructure.retrieval.sparse_retriever import (
    BM25SparseRetriever,
    tokenize_financial_text,
)


def test_tokenize_financial_text() -> None:
    # 1. Financial notation & SEC items
    tokens = tokenize_financial_text("In Item 1A, revenue was $391,035 million in 2024 (up 2%).")
    assert "item_1a" in tokens
    assert "revenue" in tokens
    assert "391" in tokens or "391035" in tokens or "2024" in tokens
    assert "2024" in tokens
    assert "million" in tokens

    # 2. Quarters normalization
    tokens2 = tokenize_financial_text("For Q3 and 4Q FY24 results")
    assert "q3" in tokens2
    assert "q4" in tokens2

    # 3. Empty text
    assert tokenize_financial_text("") == []


@pytest.mark.asyncio
async def test_bm25_indexing_and_search() -> None:
    retriever = BM25SparseRetriever(k1=1.5, b=0.75, exact_boost=2.0)

    chunks = [
        DocumentChunk(
            id="chunk-1",
            document_id="doc-1",
            document_version_id="ver-1",
            page_number=1,
            chunk_index=0,
            content="Apple reported total revenue of $391 billion in fiscal 2024.",
            section_path="Item 8. Financial Statements",
            metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
        ),
        DocumentChunk(
            id="chunk-2",
            document_id="doc-2",
            document_version_id="ver-2",
            page_number=10,
            chunk_index=0,
            content="Microsoft cloud revenue and Azure growth accelerated in 2024.",
            section_path="Item 7. MD&A",
            metadata={"ticker_symbol": "MSFT", "fiscal_year": 2024},
        ),
        DocumentChunk(
            id="chunk-3",
            document_id="doc-1",
            document_version_id="ver-1",
            page_number=15,
            chunk_index=1,
            content="Item 1A Risk Factors: Supply chain constraints and foreign exchange volatility.",
            section_path="Item 1A. Risk Factors",
            metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
        ),
    ]

    indexed_count = await retriever.index_chunks(chunks)
    assert indexed_count == 3
    assert retriever.total_documents == 3

    # Query 1: Apple revenue
    q1 = RetrievalQuery(
        raw_query="What was Apple revenue in 2024?",
        normalized_query="What was Apple revenue in 2024?",
    )
    results1 = await retriever.retrieve(q1, top_k=2)
    assert len(results1) > 0
    assert results1[0].chunk.id == "chunk-1"
    assert results1[0].sources == [RetrievalSource.SPARSE]
    assert results1[0].sparse_score is not None and results1[0].sparse_score > 0.0

    # Query 2: Risk factors in Item 1A
    q2 = RetrievalQuery(
        raw_query="What are the Item 1A risk factors?",
        normalized_query="What are the Item 1A risk factors?",
    )
    results2 = await retriever.retrieve(q2, top_k=2)
    assert len(results2) > 0
    assert results2[0].chunk.id == "chunk-3"


@pytest.mark.asyncio
async def test_bm25_metadata_filtering() -> None:
    retriever = BM25SparseRetriever()

    chunks = [
        DocumentChunk(
            id="c-aapl-2023",
            document_id="doc-aapl",
            document_version_id="ver-aapl-23",
            page_number=1,
            chunk_index=0,
            content="Revenue was $383 billion in 2023.",
            metadata={"ticker_symbol": "AAPL", "fiscal_year": 2023},
        ),
        DocumentChunk(
            id="c-aapl-2024",
            document_id="doc-aapl",
            document_version_id="ver-aapl-24",
            page_number=1,
            chunk_index=0,
            content="Revenue was $391 billion in 2024.",
            metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
        ),
    ]
    await retriever.index_chunks(chunks)

    # Filter strictly for 2024
    q = RetrievalQuery(
        raw_query="revenue",
        normalized_query="revenue",
        filters=RetrievalFilter(fiscal_years=[2024]),
    )
    results = await retriever.retrieve(q, top_k=10)
    assert len(results) == 1
    assert results[0].chunk.id == "c-aapl-2024"


@pytest.mark.asyncio
async def test_bm25_delete_and_empty() -> None:
    retriever = BM25SparseRetriever()
    assert await retriever.retrieve(RetrievalQuery(raw_query="test", normalized_query="test")) == []

    chunk = DocumentChunk(
        id="c-temp",
        document_id="doc-temp",
        document_version_id="ver-temp",
        page_number=1,
        chunk_index=0,
        content="Temporary document content.",
    )
    await retriever.index_chunks([chunk])
    assert retriever.total_documents == 1

    deleted = await retriever.delete_by_document_id("doc-temp")
    assert deleted is True
    assert retriever.total_documents == 0
    assert await retriever.health_check() is True
