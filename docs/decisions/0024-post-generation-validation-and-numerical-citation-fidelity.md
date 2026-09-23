# 24. 8-Stage Post-Generation Validation and Numerical/Citation Fidelity

Date: 2026-08-22

## Status

Accepted

## Context

Generative models may occasionally introduce unverified numbers (e.g. confusing millions with billions), fabricate citation markers (e.g. `[C99]` when only `[C1]`-`[C5]` exist), or make speculative claims.

A zero-hallucination policy requires an active, deterministic validation barrier before any LLM response is presented to end users.

## Decision

We implement an 8-stage deterministic `AnswerValidator` that audits every synthesized output:

1. **Stage 1 (Schema & Completeness)**: Rejects empty summaries or missing detailed bodies.
2. **Stage 2 (Citation Marker Audit)**: Regex extracts all `[C\d+]` markers and asserts they belong to the verified citation set. Rejects unknown markers like `[C99]`.
3. **Stage 3 (Claim Reference Audit)**: Asserts all referenced claim IDs exist in the `AnswerPackage`.
4. **Stage 4 (Numerical Fidelity Audit)**: Extracts numbers and percentage deltas from the generated text and verifies them against the pool of verified facts and calculations within tolerance.
5. **Stage 5 (Grounding Consistency)**: Asserts that partially-grounded packages disclose limitations.
6. **Stage 6 (Answerability Consistency)**: Verifies that partially-answerable inquiries state what is missing.
7. **Stage 7 (Unsupported Content Detection)**: Flags speculative phrases ("I predict", "guaranteed to").
8. **Stage 8 (Style / Length Compliance)**: Enforces style-specific token/character bounds.

Any fatal or retryable violation flags the response as invalid, triggering a constrained retry or safe deterministic fallback.

## Consequences

### Positive
- Guarantees that no fabricated numbers or phantom citations reach the user.
- Enforces strict compliance with financial regulations and audit standards.

### Negative / Trade-offs
- Slight increase in processing time for regex and numerical set matching.
