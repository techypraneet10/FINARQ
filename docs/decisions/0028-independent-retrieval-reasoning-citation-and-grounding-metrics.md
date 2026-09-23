# 0028. Independent Retrieval, Reasoning, Citation, and Grounding Metrics

Date: 2026-08-22  
Status: Accepted

## Context
Standard RAG evaluation metrics often lump retrieval and generation together, masking intermediate pipeline failures. In financial systems:
- Retrieval must be evaluated via ranking and relevance metrics (Recall@K, Precision@K, MRR, NDCG@K).
- Fact extraction must measure exact matches, precision, recall, and scale/period attributes.
- Numerical reasoning must measure exact mathematical formula and operand correctness.
- Citations must verify that cited sources actually support associated claims.
- Evidence grounding must measure grounded answer rates and unsupported claim rates.

## Decision
We decouple evaluation metrics across specialized layer evaluators:
1. **`RetrievalEvaluator`**: Computes Recall@K, Precision@K, HitRate@K, MRR, and NDCG@K for K in [1, 3, 5, 10], and supports strategy ablation (Dense vs Sparse vs Hybrid vs Hybrid+Rerank) with failure categorization (`NO_RELEVANT_CHUNK`, `LOW_RANK_RELEVANCE`).
2. **`ReasoningEvaluator`**: Computes fact extraction F1 and deterministic calculation accuracy, verifying inputs, formulas, outputs, and zero-division handling.
3. **`CitationEvaluator`**: Measures citation precision (does source evidence support claim?), citation recall, citation validity, and completeness.
4. **`GroundingEvaluator`**: Measures grounded answer rate, unsupported claim rate, and grounding failure rate.
5. **`AnswerEvaluator`**: Measures factual faithfulness, numerical fidelity, refusal correctness, and prompt injection resistance.
6. **Composite Score**: Consolidated weighted scorecard:
   $$Score_{composite} = 0.20 \times Retrieval + 0.25 \times Reasoning + 0.20 \times Citations + 0.15 \times Grounding + 0.20 \times Answer$$

## Consequences
### Positive
- Transparent, uncoupled performance tracking across every pipeline boundary.
- Objective, mathematical metrics prioritized over subjective fluency.
- Direct identification of retrieval bottlenecks vs synthesis errors.

### Negative / Trade-offs
- Multiple metric computations per evaluation case, requiring structured evaluation fixtures.
