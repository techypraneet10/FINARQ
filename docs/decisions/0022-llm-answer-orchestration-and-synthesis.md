# 22. LLM Answer Orchestration & Synthesis Architecture

Date: 2026-08-22

## Status

Accepted

## Context

In complex corporate and financial intelligence platforms, Large Language Models (LLMs) are often mistakenly used as monolithic, all-in-one query engines. However, treating an LLM as the authoritative factual database or mathematical calculator results in hallucinations, numerical drift, fabricated citations, and ungrounded statements.

To maintain strict enterprise compliance and absolute fidelity to source disclosures, the architecture requires an explicit division of responsibilities:
- Phase 2 retrieves relevant multi-period and tabular evidence.
- Phase 3 extracts structured facts, performs deterministic `Decimal` calculations, detects conflicts, and validates grounding.
- Phase 4 synthesizes verified results into clear, professional, and cited natural language answers.

## Decision

We implement a strictly controlled **Answer Orchestration Pipeline** where the LLM functions solely as an instruction-following synthesis and presentation engine downstream of Phase 3 reasoning.

1. **Strict Dependency Hierarchy**:
   - `User Query` $\to$ `RetrievalService` $\to$ `ReasoningService` $\to$ `AnswerPackage` $\to$ `AnswerabilityGate` $\to$ `ContextBuilder` $\to$ `PromptBuilder` $\to$ `LLMProvider` $\to$ `AnswerValidator` $\to$ `ResponseRenderer` $\to$ `AnswerResponse`.
2. **Authoritative Primacy**:
   - The LLM is strictly prohibited from overriding verified Phase 3 facts, inventing citations, or performing independent arithmetic.
3. **Controlled Presentation Styles**:
   - The engine supports user-selectable presentation styles (`CONCISE`, `STANDARD`, `DETAILED`, `ANALYTICAL`) that alter formatting without mutating factual numbers or citations.

## Consequences

### Positive
- Prevents LLM hallucinations from contaminating factual answers.
- Preserves 100% auditable provenance from source PDF/tables to natural language answers.
- Eliminates floating-point calculation drift.

### Negative / Trade-offs
- Adds a small validation latency overhead (~50-100ms) to audit synthesized outputs before returning them to clients.
