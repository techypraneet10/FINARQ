# ADR 0015: Cross-Encoder Reranking and Latency Safety Bounds

## Status
Accepted

## Context
First-stage retrieval (dense + sparse) optimizes for recall across tens of thousands of chunks. To achieve high precision for complex multi-period and comparative financial reasoning, a cross-encoder model scoring query-document pairs jointly is required. However, cross-encoder inference is computationally heavy ($O(N)$ transformer forward passes).

## Decision
1. **RerankerProtocol Abstraction**: Defined a clean domain interface `RerankerProtocol` with `rerank(query, candidates, top_k)` and `health_check()`.
2. **Deterministic MockReranker**: Implemented `MockReranker` using deterministic financial token, metric, and entity overlap metrics for fast, predictable CI/CD and offline evaluation benchmarks.
3. **CrossEncoder Adapter**: Implemented `CrossEncoderReranker` using HuggingFace / `sentence-transformers` (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`) with lazy loading and sigmoid score normalization.
4. **Safety Bounding**: Hard-capped candidate pool input size to $N \le 50$ (`rerank_top_k`), preventing runaway GPU/CPU inference latencies during heavy search traffic.
5. **Resilient Degradation**: If reranking fails or encounters timeout/memory errors, the pipeline gracefully falls back to the fused RRF ranking without aborting the user request.

## Consequences
- **Positive**: High precision on top-ranked evidence; predictable bounded compute latencies; zero external dependencies required during unit testing.
- **Negative**: Adds optional runtime dependency on `sentence-transformers` for production environments.
