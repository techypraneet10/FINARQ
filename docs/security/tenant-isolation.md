# Financial RAG Platform — Multi-Tenant Isolation Architecture

## 1. Architectural Invariant
**Tenant isolation is a fundamental, non-negotiable security boundary.**
Under no circumstances may Tenant A discover, query, infer, or synthesize responses using data, metadata, vectors, or audit logs belonging to Tenant B.

---

## 2. Multi-Layer Defense-in-Depth Isolation

| Architectural Tier | Isolation Enforcement Mechanism |
| :--- | :--- |
| **API Gateway / Dependency** | `get_current_principal` validates JWT token and extracts immutable `tid` claim. Client-provided tenant request headers or query overrides are ignored. |
| **Application Services** | Services pass `tenant_id` as an explicit, required parameter to all repository queries, vector searches, and storage lookups. |
| **PostgreSQL Database** | All repository SELECT / UPDATE / DELETE queries include explicit parameterized `WHERE tenant_id = :tenant_id` clauses. |
| **Qdrant Vector Store** | All search queries inject a mandatory `models.FieldCondition(key="tenant_id", match=models.MatchValue(value=tenant_id))`. As defense-in-depth, retrieved vector points verify `payload.tenant_id == expected_tenant_id` before inclusion in candidate pools. |
| **Object Storage (Filesystem/S3)** | Object storage paths are strictly prefixed by tenant ID: `tenants/{tenant_id}/documents/{document_id}/versions/{version_id}/{filename}`. |
| **Hybrid BM25 Sparse Index** | Lexical retrieval filters candidates against tenant-scoped chunk repositories prior to fusion and reranking. |
| **Reasoning & Answer Synthesis** | Context builders construct prompt context solely from verified `AnswerPackage` facts grounded in caller tenant documents. |
| **Audit Logs** | `AuditEventRepository.list_by_tenant` queries strictly filter by `tenant_id == principal.tenant_id`. |

---

## 3. Cross-Tenant Negative Testing Invariants

1. **Direct Document Lookup**: Requesting a known Tenant B document UUID with Tenant A credentials returns `HTTP 404 Not Found`.
2. **Version / Chunk / Page Lookup**: Requesting sub-document resources across tenant boundaries returns `HTTP 404 Not Found`.
3. **Vector Similarity Search**: Dense vector search by Tenant A never returns vector points indexed by Tenant B, regardless of query semantics or similarity scores.
4. **Ingestion Job Status & Retry**: Ingestion jobs registered by Tenant B are completely invisible and un-retryable by Tenant A.
5. **Audit Trail Access**: Querying `/api/v1/audit-events` returns only audit events with matching `tenant_id`.
