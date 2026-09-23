# ADR 0044: Service Level Objectives (SLOs) and Error Budget Policy

## Status
Accepted

## Context
Clear quantitative reliability targets are required to balance feature velocity with production stability and regulatory compliance.

## Decision
We establish explicit Service Level Indicators (SLIs), Service Level Objectives (SLOs), and an Error Budget Policy:
1. **API Availability SLO**: 99.9% of valid HTTP requests to `/api/v1/*` must return non-5xx status codes over a 30-day rolling window.
2. **Query Latency SLOs**:
   - Simple Retrieval: p95 latency < 500ms.
   - Verified Answer Synthesis: p95 latency < 3500ms.
3. **Ingestion Throughput SLO**: 95% of standard 10-K filings (under 100 pages) must be parsed, indexed, and queryable within 120 seconds.
4. **Data Isolation SLO**: 100% zero cross-tenant data leakage.
5. **Error Budget Policy**:
   - If error budget consumption exceeds 50% over a 7-day window, non-critical feature releases are deprioritized in favor of reliability engineering.
   - If error budget is exhausted (100% burned), feature deployments are frozen until stability is restored.

## Consequences
### Positive
- Objective, measurable operational criteria.
- Prevents technical debt accumulation and unconstrained outages.
