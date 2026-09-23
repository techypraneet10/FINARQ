# Production Financial RAG Platform — Grafana Dashboards Specification

This document defines the 7 production operational dashboards for monitoring, SLO tracking, cost governance, and dependency health across the Financial RAG Platform.

---

## 1. System Health & Reliability Dashboard (`dashboard-system-health`)
**Purpose**: Executive and SRE overview of global uptime, error budgets, active degradations, and overall platform SLOs.

### Panels & PromQL Queries
1. **API Availability & Error Rate (% 5xx vs 2xx/4xx)**
   ```promql
   sum(rate(http_requests_total{status=~"5.."}[5m]))
   /
   sum(rate(http_requests_total[5m])) * 100
   ```
2. **P50 / P95 / P99 End-to-End API Latency**
   ```promql
   histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
   histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
   histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
   ```
3. **Dependency Health Status Grid**
   ```promql
   financial_rag_dependency_health_status
   ```
4. **Active Circuit Breaker States (0=CLOSED, 1=HALF_OPEN, 2=OPEN)**
   ```promql
   financial_rag_circuit_breaker_state
   ```
5. **Fallback Activation Rate by Component**
   ```promql
   sum(rate(financial_rag_fallbacks_total[5m])) by (component)
   ```

---

## 2. Ingestion Pipeline Observability (`dashboard-ingestion`)
**Purpose**: In-depth monitoring of batch and real-time financial document parsing, OCR, chunking, and embedding.

### Panels & PromQL Queries
1. **Active vs Completed Ingestion Jobs**
   ```promql
   financial_rag_ingestion_jobs_active
   sum(increase(financial_rag_ingestion_jobs_total[1h])) by (status)
   ```
2. **Stage-by-Stage Processing Duration (P95)**
   ```promql
   histogram_quantile(0.95, sum(rate(financial_rag_ingestion_stage_duration_ms_bucket[15m])) by (le, stage))
   ```
3. **Chunking & Table Extraction Throughput**
   ```promql
   sum(rate(financial_rag_chunks_created_total[5m]))
   sum(rate(financial_rag_tables_extracted_total[5m]))
   ```
4. **Embedding Generation Throughput & Provider Latency**
   ```promql
   sum(rate(financial_rag_embedding_requests_total[5m])) by (provider)
   histogram_quantile(0.95, sum(rate(financial_rag_embedding_latency_seconds_bucket[5m])) by (le, provider))
   ```
5. **Ingestion Stage Failure Breakdown**
   ```promql
   sum(increase(financial_rag_ingestion_stage_duration_ms_count{status="failure"}[1h])) by (stage)
   ```

---

## 3. Retrieval & Reranking Performance (`dashboard-retrieval`)
**Purpose**: Visibility into hybrid dense vector search, sparse BM25 retrieval, reciprocal rank fusion (RRF), and cross-encoder reranking.

### Panels & PromQL Queries
1. **Hybrid Retrieval Mode Distribution (dense+sparse vs fallback modes)**
   ```promql
   sum(rate(financial_rag_retrieval_queries_total[5m])) by (mode)
   ```
2. **Retrieval Latency Heatmap & Quantiles**
   ```promql
   histogram_quantile(0.50, sum(rate(financial_rag_retrieval_duration_ms_bucket[5m])) by (le))
   histogram_quantile(0.95, sum(rate(financial_rag_retrieval_duration_ms_bucket[5m])) by (le))
   histogram_quantile(0.99, sum(rate(financial_rag_retrieval_duration_ms_bucket[5m])) by (le))
   ```
3. **Qdrant Vector DB Query Latency & Error Rate**
   ```promql
   histogram_quantile(0.95, sum(rate(financial_rag_vector_db_latency_seconds_bucket[5m])) by (le))
   sum(rate(financial_rag_vector_db_errors_total[5m]))
   ```
4. **Reranker Latency & Candidate Shrinkage**
   ```promql
   histogram_quantile(0.95, sum(rate(financial_rag_rerank_duration_ms_bucket[5m])) by (le))
   sum(rate(financial_rag_rerank_candidates_selected_total[5m])) / sum(rate(financial_rag_rerank_candidates_total[5m]))
   ```
5. **Sparse Lexical Fallback Activation Frequency**
   ```promql
   sum(rate(financial_rag_retrieval_queries_total{fallback="true"}[5m]))
   ```

---

## 4. Deterministic Reasoning & Financial Calculation (`dashboard-reasoning`)
**Purpose**: Validation and latency tracking for formula execution, conflict resolution, grounding, and answerability evaluation.

### Panels & PromQL Queries
1. **Reasoning Execution Duration by Operation**
   ```promql
   histogram_quantile(0.95, sum(rate(financial_rag_reasoning_duration_ms_bucket[5m])) by (le, operation))
   ```
2. **Arithmetic & Formula Calculation Success vs Failure Rate**
   ```promql
   sum(rate(financial_rag_reasoning_operations_total[5m])) by (operation, status)
   ```
3. **Fact Extraction & Conflict Resolution Metrics**
   ```promql
   sum(rate(financial_rag_facts_extracted_total[5m]))
   sum(rate(financial_rag_conflicts_detected_total[5m]))
   ```
4. **Answerability Classification Breakdown**
   ```promql
   sum(rate(financial_rag_answerability_evaluations_total[5m])) by (outcome)
   ```
5. **Grounding Verification Success Rate**
   ```promql
   sum(rate(financial_rag_grounding_checks_total{status="grounded"}[5m]))
   /
   sum(rate(financial_rag_grounding_checks_total[5m])) * 100
   ```

---

## 5. LLM Synthesis & Cost Governance (`dashboard-llm-cost`)
**Purpose**: Token consumption tracking, financial LLM model latency, estimated operational expenses, and validation rejection rates.

### Panels & PromQL Queries
1. **Token Ingestion & Generation Rate**
   ```promql
   sum(rate(financial_rag_llm_input_tokens_total[5m])) by (model)
   sum(rate(financial_rag_llm_output_tokens_total[5m])) by (model)
   ```
2. **Cumulative & Hourly Estimated Cost (USD)**
   ```promql
   sum(increase(financial_rag_llm_cost_usd_total[1h])) by (model)
   sum(financial_rag_llm_cost_usd_total)
   ```
3. **LLM Provider Latency (P50, P95, P99)**
   ```promql
   histogram_quantile(0.50, sum(rate(financial_rag_llm_latency_seconds_bucket[5m])) by (le, model))
   histogram_quantile(0.95, sum(rate(financial_rag_llm_latency_seconds_bucket[5m])) by (le, model))
   histogram_quantile(0.99, sum(rate(financial_rag_llm_latency_seconds_bucket[5m])) by (le, model))
   ```
4. **Post-Synthesis Validation Rule Failures**
   ```promql
   sum(rate(financial_rag_validation_checks_total{status="invalid"}[5m])) by (rule)
   ```
5. **Deterministic Fallback vs Synthesized Response Ratio**
   ```promql
   sum(rate(financial_rag_fallbacks_total{component="answer_synthesis"}[5m]))
   /
   sum(rate(financial_rag_answers_generated_total[5m])) * 100
   ```

---

## 6. Resilience, Retries & Circuit Breakers (`dashboard-resilience`)
**Purpose**: Fault isolation, automated retry loops, circuit breaker health, and graceful degradation monitoring.

### Panels & PromQL Queries
1. **Circuit Breaker State Timeline**
   ```promql
   financial_rag_circuit_breaker_state
   ```
2. **Circuit Breaker Trip & Transition Rate**
   ```promql
   sum(rate(financial_rag_circuit_breaker_transitions_total[5m])) by (component, to_state)
   ```
3. **Fast-Fail Rejection Rate (Circuit Open Rejections)**
   ```promql
   sum(rate(financial_rag_circuit_breaker_rejections_total[5m])) by (component)
   ```
4. **Retry Attempts by Component, Reason & Outcome**
   ```promql
   sum(rate(financial_rag_retries_total[5m])) by (component, reason, status)
   ```
5. **Retry Exhaustion Rate (Permanent Failures)**
   ```promql
   sum(rate(financial_rag_retries_total{status="exhausted"}[5m])) by (component)
   ```

---

## 7. Real-Time Streaming & SSE Transport (`dashboard-streaming`)
**Purpose**: Progressive SSE streaming latency, event emission rates, client disconnects, and connection durability.

### Panels & PromQL Queries
1. **Active Concurrent SSE Connections**
   ```promql
   financial_rag_active_sse_connections
   ```
2. **SSE Event Emission Rate by Type**
   ```promql
   sum(rate(financial_rag_sse_events_total[5m])) by (event_type)
   ```
3. **Time-To-First-Token (TTFT) Latency (P50, P95)**
   ```promql
   histogram_quantile(0.50, sum(rate(financial_rag_streaming_ttft_seconds_bucket[5m])) by (le))
   histogram_quantile(0.95, sum(rate(financial_rag_streaming_ttft_seconds_bucket[5m])) by (le))
   ```
4. **Stream Duration (P50, P95, P99)**
   ```promql
   histogram_quantile(0.95, sum(rate(financial_rag_sse_stream_duration_ms_bucket[5m])) by (le))
   ```
5. **Premature Client Disconnect Rate**
   ```promql
   sum(rate(financial_rag_sse_disconnects_total[5m]))
   ```
