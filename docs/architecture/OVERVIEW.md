# Financial RAG Platform - Architecture Overview

## Overview
The Financial RAG Platform is an enterprise-grade document intelligence system designed for accurate, verifiable, and numerically precise question answering across complex financial documents (such as SEC 10-K, 10-Q, 8-K filings, annual reports, earnings call transcripts, and loan agreements).

## Architectural Pillars

1. **Grounded Evidence Over LLM Hallucination**
   - The platform strictly enforces that the LLM cannot state facts without linking to extracted document evidence.
   - Grounding validation checks will reject or flag unverified claims.

2. **Deterministic Arithmetic**
   - Ratios, percentages, EBITDA adjustments, and YoY growth calculations are computed by deterministic code or safe calculation engines, never by raw generative model text completions.

3. **Multi-Stage Retrieval**
   - Combines dense semantic vector search (Qdrant) with sparse keyword retrieval (BM25) and cross-encoder reranking to ensure high precision over complex financial terminology and tabular data.

4. **Clean Layered Architecture**
   - Domain layer has zero external dependencies.
   - Application layer defines orchestrators and ports.
   - Infrastructure layer implements adapters for databases, vector indices, and external model APIs.
   - API layer handles HTTP transport, serialization, and status code translation.
