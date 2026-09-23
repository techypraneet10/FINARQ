# 23. Structured LLM Output and Claim Reference Architecture

Date: 2026-08-22

## Status

Accepted

## Context

Unstructured text generation from LLMs often suffers from ambiguous claim attribution, missing citations, or arbitrary structural variations that prevent programmatic post-validation. 

To audit and guarantee that the LLM only asserts claims and citations derived from the `AnswerPackage`, we require a strongly-typed schema contract for model outputs.

## Decision

We enforce structured output generation using the `LLMAnswerOutput` schema contract:

1. **Schema Definition**:
   - `summary: str`: Executive summary with bracketed citation markers.
   - `detailed_answer: str`: Comprehensive answer text with embedded citation markers.
   - `sections: list[LLMAnswerSection]`: Structured subsections.
   - `calculation_explanation: str | None`: Verbatim calculation breakdown from verified calculations.
   - `cited_claim_ids: list[str]`: List of referenced Phase 3 claim identifiers.
   - `citation_markers: list[str]`: List of used citation markers (e.g. `[C1]`, `[C2]`).
   - `limitations_disclosed: list[str]`: List of disclosed missing periods/metrics.
   - `warnings: list[str]`: List of highlighted caveats or conflicts.
2. **Provider-Agnostic Validation**:
   - The output is validated immediately upon arrival using deterministic schema deserialization. Any malformed output triggers a bounded correction retry or safe fallback.

## Consequences

### Positive
- Enables deterministic, programmatic verification of citations, numbers, and claims.
- Decouples structured generation from UI/presentation formatting.

### Negative / Trade-offs
- Requires LLM providers to support structured schema generation or reliable JSON formatting.
