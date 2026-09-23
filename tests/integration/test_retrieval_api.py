"""Integration tests for POST /api/v1/retrieval/search API endpoint."""

import pytest
from fastapi.testclient import TestClient

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever


@pytest.mark.asyncio
async def test_retrieval_search_api_endpoint(client: TestClient) -> None:
    # Seed a test chunk into shared BM25 index
    test_chunk = DocumentChunk(
        id="api-test-chunk-1",
        document_id="doc-api-test",
        document_version_id="ver-api-test",
        page_number=1,
        chunk_index=0,
        chunk_type=ChunkType.TEXT,
        content="Apple reported record quarterly revenue of $94.9 billion for Q4 2024.",
        section_path="Item 8 > Results",
        metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024, "fiscal_period": "Q4"},
    )
    await bm25_retriever.index_chunks([test_chunk])

    # Execute Search API request
    payload = {
        "query": "What was Apple revenue in Q4 2024?",
        "filters": {
            "ticker_symbols": ["AAPL"],
            "fiscal_years": [2024],
        },
        "top_k": 5,
        "use_reranker": True,
    }

    response = client.post("/api/v1/retrieval/search", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "query_id" in data
    assert data["raw_query"] == payload["query"]
    assert data["query_type"] == "factual"
    assert "AAPL" in data["signals"]["tickers"]
    assert 2024 in data["signals"]["fiscal_years"]
    assert "revenue" in data["signals"]["metrics"]
    assert "retrieval_strategy" in data
    assert "execution_stages" in data
    assert data["evidence_count"] >= 1

    first_item = data["evidence"][0]
    assert "chunk_id" in first_item
    assert "document_id" in first_item
    assert "document_version_id" in first_item
    assert "page_numbers" in first_item
    assert "content" in first_item
    assert "retrieval_sources" in first_item
    assert "provenance" in first_item
    assert first_item["provenance"]["document_id"] == "doc-api-test"
    assert "timing_ms" in data
    assert "total" in data["timing_ms"]


def test_retrieval_search_api_validation(client: TestClient) -> None:
    # 1. Query too short
    resp_short = client.post("/api/v1/retrieval/search", json={"query": "a"})
    assert resp_short.status_code in [400, 422]

    # 2. Invalid top_k
    resp_invalid_k = client.post(
        "/api/v1/retrieval/search", json={"query": "Valid query", "top_k": 0}
    )
    assert resp_invalid_k.status_code in [400, 422]
