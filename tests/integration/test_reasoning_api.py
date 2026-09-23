"""Integration tests for POST /api/v1/reasoning/answer-package API endpoint."""

import pytest
from fastapi.testclient import TestClient

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever


@pytest.mark.asyncio
async def test_reasoning_answer_package_api_endpoint(client: TestClient) -> None:
    # Seed financial table chunk
    test_chunk = DocumentChunk(
        id="api-reasoning-chunk-1",
        document_id="doc-apple-10k-2024",
        document_version_id="ver-apple-2024",
        page_number=45,
        chunk_index=0,
        chunk_type=ChunkType.TABLE,
        content="""### Consolidated Statements of Operations (in millions)
| Metric | 2024 | 2023 |
| --- | --- | --- |
| Total net sales | 391,035 | 383,285 |
| Net income | 93,736 | 96,995 |
""",
        section_path="Item 8 > Financial Statements",
        metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
    )
    await bm25_retriever.index_chunks([test_chunk])

    payload = {
        "query": "What was Apple's total net sales in 2024?",
        "filters": {
            "ticker_symbols": ["AAPL"],
            "fiscal_years": [2024],
        },
        "top_k": 5,
        "use_reranker": False,
    }

    response = client.post("/api/v1/reasoning/answer-package", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert "package_id" in data
    assert "query_id" in data
    assert data["answerability"] == "answerable"
    assert "reasoning_plan" in data
    assert len(data["facts"]) >= 1
    assert len(data["claims"]) >= 1
    assert len(data["citations"]) >= 1
    assert data["grounding_validation"]["status"] == "grounded"
    assert data["grounding_validation"]["validation_passed"] is True

    # Check fact details
    first_fact = data["facts"][0]
    assert "fact_id" in first_fact
    assert "metric" in first_fact
    assert "value" in first_fact
    assert "391035000000" in first_fact["value"]["numeric_value"]
    assert first_fact["document_id"] == "doc-apple-10k-2024"
    assert first_fact["page_number"] == 45


def test_reasoning_api_validation_errors(client: TestClient) -> None:
    # 1. Query too short
    resp_short = client.post("/api/v1/reasoning/answer-package", json={"query": "a"})
    assert resp_short.status_code in [400, 422]

    # 2. Invalid top_k
    resp_k = client.post(
        "/api/v1/reasoning/answer-package", json={"query": "Valid financial query", "top_k": 0}
    )
    assert resp_k.status_code in [400, 422]
