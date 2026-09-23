# FINARQ

### Financial Document Intelligence & Verified Reasoning Platform

FINARQ is a production-oriented financial document intelligence platform designed to analyze complex financial documents and provide **verifiable, citation-backed answers with deterministic numerical reasoning**.

The platform is built around a simple principle:

> **The LLM is not the source of truth.**

Source documents provide the evidence, deterministic services perform financial calculations, and every factual response is validated against its supporting document chunks.

---

## Features

- Financial document ingestion and asynchronous processing
- PDF text extraction and OCR support
- Layout-aware document chunking
- Table-aware financial document processing
- BM25 + dense vector hybrid retrieval
- Reciprocal Rank Fusion (RRF)
- Cross-encoder reranking
- Deterministic financial calculations using `Decimal`
- Structured financial fact extraction
- Claim-to-source citation verification
- 8-stage post-generation answer validation
- Provider-agnostic LLM synthesis
- Server-Sent Events (SSE) response streaming
- Multi-tenant data isolation
- JWT authentication and 4-tier RBAC
- PII detection and protection
- Prompt-injection defenses
- Semantic and cryptographic answer caching
- Circuit breaker and retry-based resilience
- Observability and Prometheus metrics
- Docker-based local deployment
- Terraform-based AWS infrastructure
- Automated backend and frontend testing

---

## Architecture

```text
                         ┌─────────────────────┐
                         │      React 18        │
                         │    TypeScript UI     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │  Auth / RBAC / API  │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
       Document API           Query Orchestrator      Analytics
              │                     │
              ▼                     ▼
       Async Ingestion         Query Classification
              │                     │
       ┌──────┼──────┐       ┌──────┴──────┐
       ▼      ▼      ▼       ▼             ▼
      OCR   Layout  Tables  BM25       Vector Search
       │      │      │       │             │
       └──────┼──────┘       └──────┬──────┘
              ▼                     ▼
         Chunking               RRF Fusion
              │                     │
              ▼                     ▼
         Embeddings          Cross-Encoder
              │                Reranking
              │                     │
              └──────────┬──────────┘
                         ▼
                  Evidence Selection
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
      Financial Reasoning      LLM Synthesis
              │                     │
              └──────────┬──────────┘
                         ▼
                8-Stage Validation
                         │
                         ▼
                Citation Verification
                         │
                         ▼
                   Final Response
