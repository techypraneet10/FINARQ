# FINARQ Intelligence Layer — Phases 17–20 Implementation Plan

> **Document Version:** 1.0.0  
> **Status:** Approved Architecture Plan  
> **Target Subsystems:** Financial Query Compiler (Phase 17), Financial Truth Graph (Phase 18), Temporal & Accounting Consistency Engine (Phase 19), Explainable Answer Audit Trail (Phase 20)

---

## 1. Executive Summary & Vision

FINARQ is an enterprise-grade Financial Document Intelligence & Verified Reasoning Platform. Generic RAG systems rely on probabilistic LLM retrieval, hallucination-prone arithmetic, and loose citations. 

The **Intelligence Layer (Phases 17–20)** transforms FINARQ from *"financial RAG with citations"* into:
> **"A typed, auditable financial reasoning platform where natural-language financial questions are compiled into explicit execution plans, financial facts are connected to evidence and calculations through a Truth Graph, financial consistency is validated before answer generation, and users can inspect exactly why an answer was produced."**

---

## 2. Absolute Preservation Contracts (Phases 0–16)

The following existing contracts and modules are treated as production baselines and will **NOT** be rewritten, broken, or replaced:
- **Phase 0 (Core / Hexagonal Architecture):** Domain interfaces, value objects, exceptions, logging, correlation IDs, Pydantic settings.
- **Phase 1 (Document Ingestion & Normalization):** PDF parser, OCR fallback, SEC structure detection, `FinancialTableNormalizer`, semantic chunking, Qdrant/PostgreSQL storage.
- **Phase 2 (Hybrid Retrieval & Reranking):** BM25 sparse + dense vector fusion (RRF), Cross-Encoder reranker, `RankedEvidence`, `EvidenceSet`.
- **Phase 3 (Deterministic Reasoning Engine):** `DeterministicFinancialCalculator` (11 Decimal operations), `DeterministicFactExtractor`, `DeterministicClaimBuilder`, `DeterministicCitationGenerator`, `DeterministicCitationValidator`, `DeterministicGroundingValidator`, `DeterministicConflictDetector`.
- **Phase 4 (Verified LLM Answer Orchestration):** `AnswerOrchestrationService`, `AnswerabilityGate`, 8-stage `AnswerValidator`, prompt templates, bounded retries, deterministic fallback, SSE streaming.
- **Phase 5–7 (Infrastructure, Security & Ops):** Scrypt/JWT auth, 4-tier RBAC, tenant isolation, circuit breakers, worker daemons, Terraform IaC, Docker containers.
- **Phase 8/11 (Frontend Design System & UI):** React 18 / TypeScript SPA, dark-first FINARQ design tokens, `EvidenceDrawer`, `DocumentViewer`, existing components.
- **Phase 12–16 (Evaluation & Observability):** Golden benchmark framework, Prometheus metrics registry, distributed tracing spans, security controls.

---

## 3. Subsystem Architecture & Technical Design

### Phase 17: Financial Query Compiler
- **Mission:** Compile natural language financial inquiries into a strongly typed, deterministic, and validated `FinancialQueryPlan` before retrieval and reasoning.
- **Domain Models (`financial_rag.domain.entities.intelligence`):**
  - `CompiledQueryType` (11 query types including `PERCENTAGE_GROWTH`, `MARGIN_CALCULATION`, `MULTI_PERIOD_COMPARISON`, etc.)
  - `EntityReference`, `MetricReference`, `PeriodReference`
  - `CurrencyConstraint`, `ScaleConstraint`, `EvidenceRequirement`, `CalculationRequirement`
  - `FinancialQueryPlan`: Immutable dataclass representing the explicit execution plan, target operands, operations, completeness status, missing parameters, and clarification prompts.
- **Compiler Implementation (`financial_rag.infrastructure.intelligence.compiler`):**
  - `DeterministicQueryCompiler`: Rule-based deterministic compiler analyzing entities (tickers, company names), metrics (GAAP/non-GAAP terms, synonyms), temporal expressions (fiscal years, quarters, comparative spans), arithmetic operations, currency, and scale.
  - Generates schema-validated execution plan; checks answerability and incomplete inquiries (e.g. missing entity or period) without guessing.
- **Pipeline Integration:**
  `Natural Language Query -> Deterministic Compiler -> Validated QueryPlan -> Retrieval with Plan-Guided Filters -> Fact Extraction -> Temporal Consistency Engine -> Deterministic Calculator -> LLM Synthesis -> AnswerPackage`

---

### Phase 18: Financial Truth Graph
- **Mission:** Represent the full end-to-end provenance and reasoning lineage of an answer as a directed, typed knowledge & lineage graph.
- **Node Types (15):**
  - `QUERY`, `QUERY_PLAN`, `ENTITY`, `METRIC`, `PERIOD`, `FINANCIAL_FACT`, `EVIDENCE`, `DOCUMENT`, `PAGE`, `TABLE`, `CALCULATION`, `CLAIM`, `CITATION`, `ANSWER`, `VALIDATION_RESULT`
- **Edge Types (12):**
  - `ASKED`, `SPECIFIES_ENTITY`, `SPECIFIES_METRIC`, `SPECIFIES_PERIOD`, `RETRIEVED_FROM`, `SUPPORTED_BY`, `EXTRACTED_FROM`, `CALCULATED_FROM`, `PRODUCES`, `SUPPORTS`, `CITED_BY`, `VALIDATED_BY`
- **Builder (`financial_rag.infrastructure.intelligence.graph`):**
  - `TruthGraphBuilder`: Derives nodes and edges deterministically from `FinancialQueryPlan`, `EvidenceSet`, `FinancialFact`, `CalculationResult`, `Claim`, `Citation`, and `ValidationResult`.
  - Enforces strict tenant scoping (nodes and edges cannot expose cross-tenant IDs or text).
  - Fully serializable to JSON and compatible with frontend interactive graph rendering.

---

### Phase 19: Temporal & Accounting Consistency Engine
- **Mission:** Pre-validate financial facts before arithmetic and LLM synthesis to prevent temporal leakage, unit mismatch, currency contamination, and restatement confusion.
- **13 Consistency Invariant Checks:**
  1. `PERIOD_MISMATCH`
  2. `FISCAL_YEAR_MISMATCH`
  3. `FISCAL_QUARTER_MISMATCH`
  4. `ENTITY_MISMATCH`
  5. `METRIC_MISMATCH`
  6. `CURRENCY_MISMATCH` (rejection on unrequested currency mixtures, e.g. USD vs EUR)
  7. `SCALE_MISMATCH` (normalization of millions vs billions)
  8. `UNIT_MISMATCH` (percentage vs absolute)
  9. `SIGN_MISMATCH` (accounting parentheses `(1,234)` -> `-1234`)
  10. `RESTATEMENT_OR_DISCLOSURE_CONFLICT` (conflict detection with authoritative resolution basis)
  11. `DUPLICATE_EVIDENCE` (deduplication prioritizing structured tables)
  12. `TEMPORAL_LEAKAGE` (isolating target period, context comparison periods, and excluding future/irrelevant periods)
  13. `INCOMPATIBLE_FINANCIAL_VALUES`
- **Engine Implementation (`financial_rag.infrastructure.intelligence.consistency`):**
  - `TemporalAccountingConsistencyEngine`: Classifies facts into `REQUIRED`, `COMPARISON_CONTEXT`, `EXCLUDED_FUTURE`, and `EXCLUDED_IRRELEVANT`.
  - Produces `ConsistencyValidationResult` with explicit issue logs, fact role tags, and conflict resolutions.

---

### Phase 20: Explainable Answer Audit Trail & Grounding Integrity
- **Mission:** Deliver complete transparency through an interactive "WHY THIS ANSWER?" audit trail and a deterministic Grounding Integrity Score.
- **Lineage Dimensions (12 Stages):**
  1. User Question
  2. Compiled Query Plan
  3. Retrieval Scope & Filters
  4. Retrieved Evidence Pool
  5. Fact Extraction & Selection
  6. Temporal & Accounting Consistency Checks
  7. Deterministic Decimal Calculations
  8. Atomic Claims Construction
  9. Verifiable Citations
  10. Post-Generation Validation Scorecard
  11. Financial Truth Graph
  12. Final Verified Answer
- **Grounding Integrity Score (`financial_rag.infrastructure.intelligence.audit`):**
  - Deterministic 8-component score ($0.0 - 100.0\%$):
    - Evidence Coverage ($15\%$)
    - Citation Validity ($15\%$)
    - Numerical Verification ($20\%$)
    - Temporal Consistency ($15\%$)
    - Entity Consistency ($10\%$)
    - Unit/Currency Consistency ($10\%$)
    - Source Agreement ($10\%$)
    - Claim Coverage ($5\%$)
  - Explicit non-probabilistic methodology documented in detail.

---

## 4. API & Integration Design

### Additive REST Endpoints (`/api/v1`):
- `POST /api/v1/query/compile` — Compiles question into `FinancialQueryPlanResponse`
- `POST /api/v1/query/validate` — Validates query plan and flags missing parameters
- `POST /api/v1/intelligence/consistency-check` — Validates temporal/accounting consistency
- `GET /api/v1/answers/{answer_id}/truth-graph` — Retrieves Truth Graph for an answer
- `GET /api/v1/answers/{answer_id}/audit-trail` — Retrieves full 12-stage Audit Trail
- `GET /api/v1/answers/{answer_id}/integrity` — Retrieves Grounding Integrity Scorecard
- `POST /api/v1/answers/explain` — Generates on-demand explainable answer package with live audit trail, truth graph, and integrity scorecard

---

## 5. Frontend Enhancements (FINARQ Workspace)

### Preserving Existing UI / Additive Progressive Disclosure:
- **Grounding Integrity Score Indicator:** Displayed in the answer header with an interactive breakdown popover.
- **"WHY THIS ANSWER?" Button & Modal/Drawer:** Opens the 12-stage interactive audit trail.
- **Truth Graph Visualization Panel:** Interactive SVG/Card graph representing nodes and edges; clicking citations reuses existing `EvidenceDrawer`, clicking calculations opens the calculator inspector, clicking documents opens the viewer.
- **Query Plan Card:** Displays the compiled query type, entity, metric, periods, and formula.
- **Consistency Verification Panel:** Detailed breakdown of temporal matching, currency check, scale normalization, and restatement status.

---

## 6. Observability, Security & Evaluation

### Observability:
- **Metrics:** `query_compilation_total`, `query_compilation_latency_ms`, `incomplete_query_total`, `consistency_validation_total`, `consistency_issue_total`, `truth_graph_nodes_count`, `grounding_integrity_score`, `audit_trail_generation_latency_ms`.
- **Tracing Spans:** `query.compile`, `query.validate`, `truth_graph.build`, `consistency.validate`, `consistency.temporal`, `consistency.units`, `consistency.currency`, `audit_trail.build`.

### Security:
- Tenant isolation verified on all graph nodes, query plans, and audit trails.
- Zero IDOR vulnerabilities; malicious tenant access strictly rejected with 404/403.
- Untrusted document text sanitized against prompt injection.

### Evaluation:
- Dedicated benchmark dataset: `src/financial_rag/application/evaluation/datasets/financial_intelligence_eval_v1.json` containing 15 test suites.
- Evaluation metrics for query plan accuracy, entity/metric/period extraction, temporal consistency, conflict detection, truth graph completeness, and grounding integrity.

---

## 7. Implementation Sequence

1. **Step 1:** Domain models & interfaces (`domain/entities/intelligence.py`, `domain/interfaces/intelligence.py`)
2. **Step 2:** Phase 17 Query Compiler (`infrastructure/intelligence/compiler/`, tests)
3. **Step 3:** Phase 18 Truth Graph (`infrastructure/intelligence/graph/`, tests)
4. **Step 4:** Phase 19 Consistency Engine (`infrastructure/intelligence/consistency/`, tests)
5. **Step 5:** Phase 20 Audit Trail & Grounding Integrity (`infrastructure/intelligence/audit/`, tests)
6. **Step 6:** Application Service & API Endpoints (`application/intelligence/`, `api/v1/endpoints/intelligence.py`, `schemas.py`)
7. **Step 7:** Frontend Types, Client, and Components (`frontend/src/components/intelligence/`, `AskView.tsx`, `AnswerPackageView.tsx`)
8. **Step 8:** Observability & Evaluation (`infrastructure/observability/`, `datasets/financial_intelligence_eval_v1.json`)
9. **Step 9:** Documentation & ADRs (`docs/intelligence-layer/`, `docs/decisions/`, `ARCHITECTURE.md`, `README.md`)
10. **Step 10:** Comprehensive Verification (Pytest, Ruff, MyPy, Vitest, Vite Build, Security Tests, Evaluation Run)
