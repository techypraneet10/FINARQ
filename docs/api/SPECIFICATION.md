# API Specification (Phase 2)

## Overview
This document specifies the HTTP endpoints, error response schemas, and header protocols available in the Financial RAG Platform.

## Standard Headers

### Request Headers
- `X-Request-ID` (optional): Client-provided correlation ID. If omitted, the server generates a UUIDv4.

### Response Headers
- `X-Request-ID`: The correlation ID for the request.
- `X-Process-Time-Ms`: Server execution latency in milliseconds.

---

## Error Response Format
All error responses adhere to the standard JSON error envelope:

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Document with ID 'doc-123' was not found.",
    "details": {
      "resource_type": "Document",
      "resource_id": "doc-123"
    },
    "request_id": "c6218d6e-a34f-4d92-9b2f-763467bf755a"
  }
}
```

---

## Endpoints

### 1. Hybrid Retrieval Search
- **URL**: `/api/v1/retrieval/search`
- **Method**: `POST`
- **Status Code**: `200 OK`
- **Request Body**:
```json
{
  "query": "What was Apple's total revenue in fiscal year 2024?",
  "filters": {
    "ticker_symbols": ["AAPL"],
    "fiscal_years": [2024],
    "table_only": false
  },
  "top_k": 5,
  "dense_top_k": 50,
  "sparse_top_k": 50,
  "rerank_top_k": 20,
  "use_reranker": true
}
```

- **Response Body**:
```json
{
  "query_id": "a6b7152c-54b0-4128-8cac-084a390be3a5",
  "raw_query": "What was Apple's total revenue in fiscal year 2024?",
  "normalized_query": "\"What was Apple's total revenue in fiscal year 2024?\"",
  "query_type": "factual",
  "signals": {
    "tickers": ["AAPL"],
    "company_names": ["Apple"],
    "metrics": ["revenue", "total revenue"],
    "fiscal_years": [2024],
    "fiscal_periods": [],
    "sections": [],
    "statement_types": [],
    "currencies": [],
    "is_comparison": false,
    "is_table_lookup": false,
    "is_multi_period": false
  },
  "retrieval_strategy": "hybrid_dense_sparse_rrf_reranked",
  "execution_stages": [
    "query_analysis",
    "dense_retrieval",
    "sparse_retrieval",
    "candidate_fusion",
    "deduplication",
    "reranking",
    "evidence_selection",
    "validation"
  ],
  "evidence_count": 2,
  "evidence": [
    {
      "rank": 1,
      "chunk_id": "aapl-2024-chunk-101",
      "document_id": "doc-aapl-2024",
      "document_version_id": "ver-aapl-2024-v1",
      "page_number": 32,
      "page_numbers": [32],
      "chunk_type": "table",
      "content": "| Total net sales | $391,035 | $383,285 | $394,328 |",
      "section_path": "Item 8. Financial Statements > Operations",
      "table_id": "table-aapl-income-2024",
      "source_block_ids": [],
      "bounding_box": null,
      "content_hash": "4a7b...",
      "ticker": "AAPL",
      "fiscal_year": 2024,
      "fiscal_period": null,
      "retrieval_sources": ["dense_vector", "sparse_bm25"],
      "dense_score": 0.92,
      "sparse_score": 0.88,
      "fusion_score": 0.98,
      "reranker_score": 0.99,
      "final_score": 0.99,
      "provenance": {
        "document_id": "doc-aapl-2024",
        "document_version_id": "ver-aapl-2024-v1",
        "page_number": 32,
        "page_numbers": [32],
        "chunk_id": "aapl-2024-chunk-101",
        "section_path": "Item 8. Financial Statements > Operations",
        "table_id": "table-aapl-income-2024",
        "source_block_ids": []
      },
      "metadata": {
        "ticker_symbol": "AAPL",
        "fiscal_year": 2024
      }
    }
  ],
  "timing_ms": {
    "query_analysis": 1.2,
    "retrieval_io": 14.5,
    "fusion": 0.4,
    "reranking": 12.1,
    "selection": 0.3,
    "validation": 0.1,
    "total": 28.6
  },
  "fallback_occurred": false,
  "fallback_reason": null
}
```

---

### 2. Document Management
- **POST `/api/v1/documents/upload`**: Upload PDF document.
- **GET `/api/v1/documents/{document_id}`**: Get document metadata and versions.
- **GET `/api/v1/documents`**: List documents with pagination and ticker filtering.
- **DELETE `/api/v1/documents/{document_id}`**: Soft/hard delete document and associated chunks.

---

### 3. Ingestion Job Monitoring
- **GET `/api/v1/ingestion-jobs/{job_id}`**: Query ingestion status, stage progress, chunk counts, and error details.

---

### 4. Health & Readiness Probes
- **GET `/health`**: Liveness probe.
- **GET `/ready`**: Readiness probe checking PostgreSQL, Qdrant, Object Storage, and ML adapters.
