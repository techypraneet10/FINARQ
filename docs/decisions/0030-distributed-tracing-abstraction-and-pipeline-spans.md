# 0030. Distributed Tracing Abstraction and Pipeline Stage Spans

Date: 2026-08-22  
Status: Accepted

## Context
Diagnosing performance bottlenecks, failed answer synthesis, or fallback triggers in a multi-stage RAG pipeline requires granular, correlated stage timing and metadata propagation without tightly coupling the application layer to proprietary APM vendor SDKs.

## Decision
We implement a lightweight, OpenTelemetry-compatible distributed tracing abstraction:
1. **Context Propagation**: Uses Python `contextvars` (`trace_id_ctx_var`, `request_id_ctx_var`, `current_span_id_ctx_var`) to propagate request and trace correlation across asynchronous tasks and thread pools without manual parameter passing.
2. **`Tracer` & `Span` Architecture**: Thread-safe tracer providing sync (`tracer.span()`) and async (`tracer.async_span()`) context managers.
3. **Pipeline Stage Spans**:
   - `HTTP {METHOD} {ENDPOINT}` (root API span)
   - `retrieval.query_analysis`
   - `retrieval.dense_search`
   - `retrieval.sparse_search`
   - `retrieval.hybrid_fusion`
   - `retrieval.reranking`
   - `reasoning.fact_extraction`
   - `reasoning.calculation`
   - `reasoning.grounding_validation`
   - `answer.context_construction`
   - `answer.llm_generation`
   - `answer.output_validation`
   - `answer.rendering`
4. **Error & Attribute Recording**: Records execution durations in milliseconds, structured attributes, and exception status on spans.

## Consequences
### Positive
- Zero external vendor lock-in.
- Correlated request diagnostics answering *what*, *where*, *how long*, and *why*.
- OpenTelemetry format compatibility for future Jaeger, OTel Collector, or cloud exporter integration.

### Negative / Trade-offs
- Negligible sub-millisecond overhead for span creation and timing.
