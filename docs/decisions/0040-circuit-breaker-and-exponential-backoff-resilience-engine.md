# ADR 0040: Circuit Breaker and Exponential Backoff Resilience Engine

## Status
Accepted

## Context
Financial RAG workflows depend on multiple external network services: LLM API providers, embedding providers, Qdrant vector database, RDS PostgreSQL, Redis, and Object Storage. Transient network partitions or provider outages can cause cascading resource exhaustion (thread pool starvation, high latency spikes) without resilience controls.

## Decision
We implement a unified resilience module in `src/financial_rag/infrastructure/resilience/`:
1. **Three-State Circuit Breaker (`CircuitBreaker`)**:
   - `CLOSED`: Normal traffic. Tracks failure counts.
   - `OPEN`: Tripped after consecutive threshold failures (`failure_threshold`). Rejects incoming calls immediately with `CircuitBreakerOpenError` without hitting downstream.
   - `HALF_OPEN`: After cooldown timeout (`recovery_timeout_seconds`), allows trial probe requests. Recovers to `CLOSED` after consecutive successes or trips back to `OPEN` on failure.
2. **Exponential Backoff with Full Jitter (`retry_with_backoff`)**:
   - Bounded exponential backoff with randomized jitter to prevent thundering herd problems.
   - Semantic error classification: Non-retryable exceptions (validation errors, 4xx client errors, permission denials) fail fast without retrying.

## Consequences
### Positive
- Prevents cascading service failures during external vendor outages.
- Drastically reduces tail latency during downstream saturation.
