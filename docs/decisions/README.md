# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) that capture significant architectural decisions, their context, and consequences.

## When to write an ADR

An ADR is required when a decision:
1. Introduces or replaces a major library, framework, or architectural pattern.
2. Defines or modifies cross-cutting domain/application boundaries.
3. Modifies data storage, vector indexing, or retrieval paradigms.
4. Alters security, authentication, or configuration paradigms.

## Naming Convention

Format: `NNNN-short-title.md` (e.g., `0001-record-architecture-decisions.md`).

## Status Values

- **Proposed**: Under review and team evaluation.
- **Accepted**: Approved and actively followed in implementation.
- **Rejected**: Evaluated and discarded (with documented rationale).
- **Deprecated**: Previously accepted but no longer applicable.
- **Superseded**: Replaced by a subsequent ADR (link provided).

## ADR Template Format

```markdown
# [Number]. [Title]

Date: YYYY-MM-DD
Status: [Proposed | Accepted | Rejected | Deprecated | Superseded]

## Context
What is the background and the problem being solved?

## Decision
What is the chosen approach and why?

## Consequences
### Positive
- Benefit 1
- Benefit 2

### Negative / Trade-offs
- Trade-off 1
- Mitigation
```

## Index of Decisions

- [0001 - Record Architecture Decisions](0001-record-architecture-decisions.md)
- [0002 - Layered Clean Architecture](0002-layered-clean-architecture.md)
- [0003 - Configuration Management Strategy](0003-configuration-management-strategy.md)
- [0004 - Error Handling and Structured Logging](0004-error-handling-and-logging.md)
- [0005 - Hybrid Document Parsing and OCR Strategy](0005-hybrid-document-parsing-and-ocr-strategy.md)
- [0006 - Financial Table Normalization and Parenthetical Negatives](0006-financial-table-normalization-and-parenthetical-negatives.md)
- [0007 - SEC Filing Structure Detection and Hierarchy](0007-sec-filing-structure-detection-and-hierarchy.md)
- [0008 - Structure-Aware Semantic Chunking](0008-structure-aware-semantic-chunking.md)
- [0009 - Provenance Lineage and Vector Payload Contract](0009-provenance-lineage-and-vector-payload-contract.md)
- [0010 - Relational Persistence and Alembic Migrations](0010-relational-persistence-and-alembic-migrations.md)
- [0011 - Object Storage Abstraction and Security](0011-object-storage-abstraction-and-security.md)
- [0012 - Asynchronous Ingestion Orchestration and Lifecycle](0012-asynchronous-ingestion-orchestration-and-lifecycle.md)
- [0013 - Sparse Retrieval Engine and Domain Tokenization](0013-sparse-retrieval-technology.md)
- [0014 - Hybrid Candidate Fusion via Reciprocal Rank Fusion (RRF)](0014-hybrid-fusion-and-score-normalization.md)
- [0015 - Cross-Encoder Reranking and Latency Safety Bounds](0015-cross-encoder-reranking-and-safety-bounds.md)
- [0016 - Evidence Selection and Provenance Preservation Contract](0016-evidence-selection-and-provenance-preservation.md)
- [0017 - Retrieval Evaluation Benchmark and Quality Metrics](0017-retrieval-evaluation-benchmark-and-metrics.md)
- [0018 - Deterministic Financial Reasoning and Decimal Precision Arithmetic](0018-deterministic-financial-reasoning-and-decimal-precision.md)
- [0019 - Structured Fact Representation and Fiscal Period Normalization](0019-structured-fact-representation-and-fiscal-periods.md)
- [0020 - Verifiable Citation Mapping and Grounding Validation](0020-verifiable-citation-mapping-and-grounding-validation.md)
- [0021 - AnswerPackage Contract and Answerability State Machine](0021-answer-package-contract-and-answerability-state-machine.md)
- [0022 - LLM Answer Orchestration & Synthesis Architecture](0022-llm-answer-orchestration-and-synthesis.md)
- [0023 - Structured LLM Output and Claim Reference Architecture](0023-structured-llm-output-and-claim-reference-architecture.md)
- [0024 - 8-Stage Post-Generation Validation and Numerical/Citation Fidelity](0024-post-generation-validation-and-numerical-citation-fidelity.md)
- [0025 - Prompt Injection Defense & Untrusted Document Boundaries](0025-prompt-injection-defense-and-untrusted-data-boundaries.md)
- [0026 - Safe Deterministic Fallback and Bounded Retry Strategy](0026-safe-deterministic-fallback-and-bounded-retry-strategy.md)
- [0027 - Multi-Layered Evaluation Framework and Golden Benchmark Architecture](0027-multi-layered-evaluation-framework-and-golden-benchmark.md)
- [0028 - Independent Retrieval, Reasoning, Citation, and Grounding Metrics](0028-independent-retrieval-reasoning-citation-and-grounding-metrics.md)
- [0029 - Automated Regression Detection, Baselines, and CI Quality Gates](0029-automated-regression-detection-baselines-and-ci-quality-gates.md)
- [0030 - Distributed Tracing Abstraction and Pipeline Stage Spans](0030-distributed-tracing-abstraction-and-pipeline-spans.md)
- [0031 - Application Telemetry, Metrics Registry, and Cost Observability](0031-application-telemetry-metrics-registry-and-cost-observability.md)
- [0032 - Multi-Tenant Isolation Model](0032-multi-tenant-isolation-model.md)
- [0033 - Server-Side Authentication and JWT Lifecycle](0033-server-side-authentication-and-jwt-lifecycle.md)
- [0034 - Role-Based Access Control Matrix](0034-role-based-access-control-matrix.md)
- [0035 - Brute-Force Defense and Tiered Rate Limiting](0035-brute-force-and-rate-limiting-defense.md)
- [0036 - Immutable Audit Logging and Compliance](0036-immutable-audit-logging-and-compliance.md)
- [0037 - Fail-Fast Startup Security Invariant Validation](0037-startup-security-invariant-validation.md)
- [0038 - Multi-Stage Containerization and Non-Root Security Hardening](0038-multi-stage-containerization-and-non-root-security-hardening.md)
- [0039 - Standalone Ingestion Worker Daemon Architecture](0039-standalone-ingestion-worker-daemon-architecture.md)
- [0040 - Circuit Breaker and Exponential Backoff Resilience Engine](0040-circuit-breaker-and-exponential-backoff-resilience-engine.md)
- [0041 - Immutable Semantic Container Versioning and Zero-Downtime Deployment](0041-immutable-semantic-container-versioning-and-zero-downtime-deployment.md)
- [0042 - Infrastructure as Code Modularity and Multi-Environment Sizing](0042-infrastructure-as-code-modularity-and-multi-environment-sizing.md)
- [0043 - Deterministic Disaster Recovery and Vector Rebuild Strategy](0043-deterministic-disaster-recovery-and-vector-rebuild-strategy.md)
- [0044 - Service Level Objectives (SLOs) and Error Budget Policy](0044-service-level-objectives-and-error-budget-policy.md)
- [0045 - Observability, Correlation Context Propagation and Alert Routing](0045-observability-correlation-context-propagation-and-alert-routing.md)
- [0046 - Database Migration Lifecycle and Schema Integrity Verification](0046-database-migration-lifecycle-and-schema-integrity-verification.md)
- [0047 - Cloud Financial Model and Cost Optimization Strategy](0047-cloud-financial-model-and-cost-optimization-strategy.md)
