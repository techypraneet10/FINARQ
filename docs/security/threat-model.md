# Financial RAG Platform — Security Threat Model

## 1. Overview & Objectives
The Financial RAG Platform ingests, normalizes, indexes, retrieves, and reasons over confidential corporate financial filings (SEC Form 10-K, 10-Q, 8-K, earnings transcripts) across multiple isolated enterprise tenant organizations.

This document establishes the formal **STRIDE Threat Model**, actor definitions, asset taxonomies, and architectural trust boundaries.

---

## 2. Threat Actors

| Actor ID | Category | Access Level | Description & Motivation |
| :--- | :--- | :--- | :--- |
| **ACT-1** | **Anonymous Attacker** | Untrusted / Public Internet | External adversary probing public endpoints (`/health`, `/metrics`, `/auth/login`), attempting brute-force credential stuffing, API denial of service, or discovering unauthenticated internal endpoints. |
| **ACT-2** | **Authenticated Normal User** | Valid Tenant Account (Viewer / Member) | Legitimate user querying financial documents and generating verified summaries within assigned role permissions. |
| **ACT-3** | **Malicious Authenticated User** | Valid Tenant Account (Attacker) | Insider or compromised user attempting horizontal privilege escalation (BOLA/IDOR to access Tenant B documents/chunks) or vertical privilege escalation (elevating role to Admin/Owner). |
| **ACT-4** | **Tenant Administrator** | Tenant Admin / Owner | Privileged user within Tenant A managing users and viewing audit trails, bounded strictly from cross-tenant operations. |
| **ACT-5** | **Platform Administrator** | Cloud / Infrastructure Operator | Operational administrator monitoring node health and telemetry; isolated from plaintext document storage keys and tenant databases. |
| **ACT-6** | **Compromised Client / Stolen Token** | Exfiltrated JWT / Session | Attacker possessing a leaked access or refresh token; mitigated by token expiry (15m), sliding refresh rotation, and reuse-triggered cascade revocation. |
| **ACT-7** | **Malicious Document Author / Uploader** | Document Ingestion Source | Adversary crafting adversarial PDFs with polyglot code, decompression bombs, or indirect prompt injection instructions embedded in table cells or footnotes. |
| **ACT-8** | **Compromised LLM Provider** | External Upstream API | External LLM returning hallucinated, poisoned, or ungrounded responses; mitigated by deterministic post-generation validation and deterministic calculation fallback. |
| **ACT-9** | **Compromised Supply Chain** | Third-party Package | Vulnerability in dependencies; mitigated by minimal dependencies, lockfiles, and zero dynamic code execution (`eval`, `exec`, `pickle`). |

---

## 3. Critical Assets & Classification

1. **User Credentials & Sessions** (Confidentiality: CRITICAL, Integrity: CRITICAL)
   - Passwords (scrypt-hashed with per-user salt), JWT signing secrets, active refresh tokens.
2. **Tenant Corporate Filings & Binaries** (Confidentiality: CRITICAL, Integrity: HIGH)
   - Proprietary PDFs, historical revisions, extracted page text, raw layout dictionaries.
3. **Structured Financial Evidence & Tables** (Confidentiality: HIGH, Integrity: CRITICAL)
   - Extracted balance sheets, income statements, cash flow tables, unit/scale normalizations.
4. **Vector Embeddings & Inverted Indices** (Confidentiality: HIGH, Integrity: HIGH)
   - Dense vector points in Qdrant with tenant payload labels, BM25 token indices.
5. **Reasoning Plans & Calculation Traces** (Confidentiality: HIGH, Integrity: CRITICAL)
   - Deterministic arithmetic executions, ground truth financial facts, conflict graphs.
6. **Citations & Provenance Lineages** (Confidentiality: HIGH, Integrity: CRITICAL)
   - Character-exact source offsets, bounding box coordinates, document IDs.
7. **Synthesized Answers & Streams** (Confidentiality: HIGH, Integrity: CRITICAL)
   - Generated financial reports, real-time SSE token stream buffers.
8. **Audit Trail History** (Confidentiality: MEDIUM, Integrity: CRITICAL)
   - Immutable security event logs recording actor, tenant, IP, action, timestamp, and outcome.

---

## 4. Trust Boundaries & STRIDE Analysis

```
[ Untrusted Client / Browser ]
             │  Boundary 1: Edge / Transport (TLS, CORS, Security Headers, Rate Limiting)
             ▼
[ FastAPI Application Gateway ]
             │  Boundary 2: Authentication & RBAC (Bearer JWT, PrincipalContext, Permission Guards)
             ▼
[ Application Orchestration Layer ]
             ├── Boundary 3: Storage (Partitioned Keys: tenants/{tid}/...)
             ├── Boundary 4: Database (SQLAlchemy Parameterized Queries: WHERE tenant_id = :tid)
             ├── Boundary 5: Vector DB (Qdrant Mandatory Filter: FieldCondition(tenant_id))
             └── Boundary 6: LLM Provider (Untrusted Data Delimiters, Post-Gen Validation)
```

### STRIDE Assessment Summary:
- **Spoofing**: Mitigated by cryptographically signed HS256 JWT tokens with user/tenant claims and `WWW-Authenticate` bearer challenges.
- **Tampering**: Mitigated by SHA-256 document hashing, immutable version records, and server-side calculated arithmetic.
- **Repudiation**: Mitigated by structured `AuditEvent` persistence recording actor, tenant, IP, resource ID, action, and outcome.
- **Information Disclosure**: Mitigated by strict multi-layer tenant isolation, safe generic 404 responses for cross-tenant IDOR probes, and Pydantic `SecretStr` redaction.
- **Denial of Service**: Mitigated by sliding-window rate limiting per endpoint, 50MB file size caps, memory-bounded stream buffers, and circuit breaker fast-fails.
- **Elevation of Privilege**: Mitigated by server-side derived `PrincipalContext.permissions` matrix; client role assertions are ignored.
