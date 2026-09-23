# ADR 0032: Multi-Tenant Isolation Model Across Storage, Vector Indexes, and Pipeline

## Status
Accepted

## Context
The Financial RAG Platform processes confidential financial records for multiple distinct corporate organizations. Cross-tenant data leakage (e.g. exposing one tenant's revenue, margins, or forecasts to another tenant) is catastrophic. The architecture requires guaranteed tenant isolation across every layer:
1. Relational storage (PostgreSQL)
2. Vector storage (Qdrant)
3. Object storage (MinIO / S3 / Local filesystem)
4. Pipeline operations (Ingestion, Retrieval, Reasoning, Answer Generation)

## Decision
We implement strict, multi-layered tenant isolation enforced server-side:

1. **Relational Persistence**:
   - Every domain entity and ORM table (`documents`, `document_versions`, `document_pages`, `document_chunks`, `ingestion_jobs`, `refresh_tokens`, `audit_events`) contains an explicit `tenant_id` column.
   - All repository queries unconditionally filter by `tenant_id == :tenant_id`.

2. **Vector Database**:
   - Every indexed point payload contains `{"tenant_id": str(chunk.tenant_id)}`.
   - All dense vector searches inject an explicit `FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))`.
   - Post-search defense-in-depth filters reject any vector point not matching the authenticated tenant.

3. **Object Storage**:
   - All binary objects are prefixed with `tenants/{tenant_id}/documents/{document_id}/versions/{version_id}/{filename}`.

4. **Pipeline Scoping**:
   - `RetrievalFilter`, `RetrievalQuery`, `RankedEvidence`, `FinancialFact`, `Claim`, `Citation`, `AnswerPackage`, and `AnswerRequest` carry `tenant_id`.
   - Client requests are prohibited from specifying arbitrary tenant IDs; `principal.tenant_id` is injected server-side.

## Consequences
### Positive
- Strict mathematical boundary separating organizational data.
- Complete defense-in-depth across storage, vector database, and memory.
- Immune to Direct Object Reference (IDOR) attacks.

### Negative
- All queries and pipeline interfaces must pass `tenant_id`.
