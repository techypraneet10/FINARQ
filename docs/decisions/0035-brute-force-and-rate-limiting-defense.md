# ADR 0035: Sliding-Window Rate Limiting & Account Lockout Defense

## Status
Accepted

## Context
Exposing public financial API endpoints introduces risks of credential brute-forcing, Denial of Service (DoS), and resource exhaustion attacks against costly embedding and LLM inference endpoints.

## Decision
We implement a high-performance in-memory sliding-window rate limiter and failed login lockout mechanism:

1. **Sliding-Window Rate Limiting**:
   - `InMemoryRateLimiter` tracks timestamped access logs per client key within sliding time windows (default: 60 seconds).
   - Dynamic threshold limits per route category:
     - Authentication (`/api/v1/auth`): 30 req/min
     - Document Upload (`POST /api/v1/documents`): 20 req/min
     - Retrieval (`/api/v1/retrieval`): 60 req/min
     - Answer Synthesis (`/api/v1/answers`): 30 req/min
     - Default endpoints: 120 req/min
   - Rejections return HTTP `429 Too Many Requests` with `Retry-After` header.

2. **Brute-Force Login Lockout**:
   - Consecutive failed authentication attempts (default: 5) trigger temporary lockout (default: 15 minutes) for the client IP and email pair.
   - Successful authentication resets the failed login counter.

## Consequences
### Positive
- Protects downstream vector stores, LLM endpoints, and databases from exhaustion.
- Mitigates dictionary and brute-force password guessing attacks.
