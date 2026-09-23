# 21. AnswerPackage Contract and Answerability State Machine

Date: 2026-08-22

## Status

Accepted

## Context

Financial queries are frequently asked about metrics, companies, or time periods not covered in the ingested document corpus, or where available evidence is contradictory or insufficient. Rather than guessing, hallucinating, or failing silently, the platform must return a comprehensive, structured `AnswerPackage` with an explicit classification of answerability.

## Decision

We establish the `AnswerPackage` domain contract and a 7-state answerability state machine:
1. **Answerability States**:
   - `ANSWERABLE`: Complete supporting facts extracted, calculations succeeded, 100% grounded.
   - `PARTIALLY_ANSWERABLE`: Subset of multi-part inquiry facts available.
   - `INSUFFICIENT_EVIDENCE`: Required facts or metrics not found in corpus.
   - `CONFLICTING_EVIDENCE`: Unresolved factual contradictions between sources.
   - `AMBIGUOUS_QUERY`: Query lacks requisite temporal or metric specificity.
   - `CALCULATION_FAILED`: Mathematical edge case encountered (e.g. division by zero).
   - `GROUNDING_FAILED`: Claims failed grounding validation audit.
2. **AnswerPackage Contract**: The root payload encapsulates:
   - `raw_query` and `normalized_query`
   - `answerability` status enum and descriptive rationale
   - `reasoning_plan`
   - `facts` list with full provenance
   - `calculations` list with audit formulas
   - `reasoning_trace` with step-by-step state transitions
   - `claims` and `citations` with verification markers
   - `evidence` items with ranking metrics
   - `conflicts` and `missing_facts`
   - `grounding_validation` audit summary
   - `execution_time_ms` stage timings.

## Consequences

- **Pros**: Downstream consumers (APIs, UI, report generators) receive full transparency on data completeness, calculation formulas, and grounding confidence.
- **Cons**: Requires thorough evaluation rules across missing fact detection, conflict checking, and grounding status in the reasoning pipeline.
