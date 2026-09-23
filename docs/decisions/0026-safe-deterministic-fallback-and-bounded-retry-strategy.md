# 26. Safe Deterministic Fallback and Bounded Retry Strategy

Date: 2026-08-22

## Status

Accepted

## Context

In production environments, LLM providers may experience transient network timeouts, rate limiting, or occasional output validation failures (e.g. failing to include an exact citation or formatting malformed JSON). 

Failing with a 500 error or returning an unverified hallucination is unacceptable in financial mission-critical workloads.

## Decision

We implement a **Bounded Retry with Safe Deterministic Fallback Strategy**:

1. **Bounded Retry ($\le 1$ Retry Attempt)**:
   - If the first LLM generation attempt fails validation due to a retryable error (e.g. unknown citation marker), the engine appends a constrained correction prompt and re-invokes the provider once.
2. **Safe Deterministic Fallback**:
   - If the second attempt also fails, or if the LLM provider experiences an exception (timeout, 503 outage, malformed JSON), the system does not fail or guess.
   - It invokes `ResponseRenderer.render_deterministic_fallback()` to construct a 100% grounded response built strictly from the verified `AnswerPackage.claims`, `calculations`, and `citations`.
   - The response metadata flags `used_fallback=True` and includes diagnostic reasons in `warnings`.

## Consequences

### Positive
- Guarantees high platform availability and zero hallucination risk during upstream provider outages.
- Never traps the application in infinite retry loops.

### Negative / Trade-offs
- Fallback answers are syntactically simpler (assembled directly from structured claim templates) than natural LLM prose, though mathematically and evidentiary identical in truth.
