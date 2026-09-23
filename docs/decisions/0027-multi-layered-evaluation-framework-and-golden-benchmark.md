# 0027. Multi-Layered Evaluation Framework and Golden Benchmark Architecture

Date: 2026-08-22  
Status: Accepted

## Context
In a mission-critical financial RAG platform, evaluating the system using only a single high-level score (such as end-to-end answer text similarity or LLM judge ratings) is dangerous and inadequate. A system may perform excellent retrieval but calculate growth rates incorrectly; or perform correct arithmetic but cite the wrong document pages; or fabricate ungrounded speculative explanations.

Furthermore, evaluation datasets must be strictly versioned, deterministic, and auditable so that engineering teams can measure quality regressions without altering the underlying benchmark.

## Decision
We implement a multi-layered evaluation architecture comprising:
1. **Independent Evaluation Levels**: Evaluating 10 distinct quality and operational dimensions (Document/Ingestion quality, Retrieval quality, Fact extraction quality, Financial reasoning quality, Citation quality, Grounding quality, LLM answer quality, End-to-end quality, Operational reliability, Performance and cost).
2. **Versioned Golden Benchmark Datasets**: Standardized benchmark datasets (starting with `financial_rag_eval_v1`) containing diverse, realistic test cases across retrieval, multi-period calculations, ratios, table-vs-narrative conflicts, future unindexed periods, nonexistent metrics, and prompt injection attacks.
3. **Evaluation Run Traceability**: Every evaluation execution receives a unique `evaluation_run_id` connecting code version, prompt version, model, configuration, dataset version, and metrics.
4. **Deterministic Ground Truth Authority**: Numerical accuracy and citation validity are verified against mathematical and structural ground truth rather than subjective text heuristics.

## Consequences
### Positive
- Layer-isolated diagnoses pinpointing the exact failure stage (retrieval vs extraction vs math vs citation vs synthesis).
- Reproducible, audit-grade evaluation benchmarks.
- Zero dependency on external paid APIs for mandatory CI evaluations.

### Negative / Trade-offs
- Maintaining and versioning comprehensive test cases requires explicit schema management and manifest tracking.
