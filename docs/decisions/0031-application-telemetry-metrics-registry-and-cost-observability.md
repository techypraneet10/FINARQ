# 0031. Application Telemetry, Metrics Registry, and Cost Observability

Date: 2026-08-22  
Status: Accepted

## Context
Production financial AI platforms require continuous visibility into request rates, error distributions, component fallbacks, latency distributions (P50, P90, P95, P99), dependency availability, and LLM inference expenditures while preventing high-cardinality label explosions and sensitive data leakage.

## Decision
We implement a unified telemetry and metrics subsystem:
1. **Thread-Safe Metrics Registry (`MetricsRegistry`)**:
   - Monotonic Counters (`http_requests_total`, `error_total`, `fallback_total`).
   - Percentile Histograms (`http_request_duration_ms`, `retrieval_latency_ms`, `reasoning_latency_ms`, `llm_latency_ms`).
   - State Gauges (`dependency_up`).
2. **Low-Cardinality Enforcement**:
   - Strict dimension whitelist (`endpoint`, `status`, `provider`, `model`, `operation`, `error_type`, `strategy`, `component`).
   - Explicit prohibition of high-cardinality keys (`query`, `document_id`, `user_id`, `chunk_id`, `prompt`).
3. **Universal Error Taxonomy (`ErrorClassifier`)**:
   - Standardized error categories (`VALIDATION_ERROR`, `INGESTION_ERROR`, `RETRIEVAL_ERROR`, `REASONING_ERROR`, `CALCULATION_ERROR`, `CITATION_ERROR`, `GROUNDING_ERROR`, `LLM_ERROR`, `TIMEOUT`, `DEPENDENCY_UNAVAILABLE`, `CONFIGURATION_ERROR`, `INTERNAL_ERROR`).
4. **Configurable LLM Cost Calculator (`CostCalculator`)**:
   - Tracks input, output, and cached tokens, computing dollar costs based on dynamic model pricing tables.
5. **Metrics REST Endpoint**:
   - Exposes `GET /api/v1/metrics` returning real-time metrics, percentiles, and dependency health states.

## Consequences
### Positive
- Production-ready observability answering *how often does it fail?* and *what does it cost?*.
- Bounded memory footprint with guaranteed low cardinality.
- Full fallback and degraded dependency visibility.

### Negative / Trade-offs
- In-memory metrics reset on process restart unless scraped by Prometheus / OpenTelemetry collectors.
