# ADR 0045: Observability, Correlation Context Propagation and Alert Routing

## Status
Accepted

## Context
Diagnosing distributed issues across API handlers, background ingestion workers, vector databases, and LLMs requires unified correlation tracing and clear alert triage.

## Decision
We enforce end-to-end trace correlation and tiered alert routing:
1. **Context Variables Tracing**: Every inbound HTTP request and worker job is assigned a unique correlation ID (`request_id_ctx_var`). All logs emitted in the async context automatically include `"request_id": "<id>"`.
2. **Standard Prometheus Metrics**: Metrics registry exposes request duration histograms, active worker gauges, Qdrant search latencies, LLM token counters, and circuit breaker trip metrics at `/metrics`.
3. **Alert Tiering**:
   - **Severity 1 (Critical - PagerDuty / On-Call Paging)**: Complete API outage, database connectivity loss, active cross-tenant isolation violation, circuit breaker tripped for > 5 minutes.
   - **Severity 2 (High - Slack / Email Ticket)**: Error rate > 1%, p95 latency > 5000ms, worker backlog > 100 jobs for > 15 minutes.
   - **Severity 3 (Warning - Dashboard / Daily Digest)**: S3 storage tiering anomalies, non-urgent LLM fallback rate > 5%.

## Consequences
### Positive
- Rapid root-cause analysis via unified correlation IDs.
- Clear alert routing with zero alert fatigue on trivial warnings.
