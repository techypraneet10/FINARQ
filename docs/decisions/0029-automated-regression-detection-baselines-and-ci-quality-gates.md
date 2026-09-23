# 0029. Automated Regression Detection, Baselines, and CI Quality Gates

Date: 2026-08-22  
Status: Accepted

## Context
As the platform evolves (new embedding models, chunking refinements, prompt revisions, or reranker updates), regressions must be detected before deployment. Continuous integration must enforce hard quality gates without depending on paid cloud APIs or volatile benchmarks.

## Decision
We implement automated regression detection and CI quality gates:
1. **Immutable Baseline Management**: Approved evaluation runs are persisted to disk as versioned baselines (`baseline_<dataset_version>.json`). Baselines are never overwritten automatically and require deliberate approval (`set-baseline`).
2. **Configurable Regression Detection**: The `RegressionDetector` compares current evaluation metrics against the active baseline:
   - Calculation accuracy drop: strict 0.00 tolerance (`CRITICAL`).
   - Grounded answer rate drop $> 2\%$: `CRITICAL`.
   - Citation precision drop $> 2\%$: `WARNING` / $> 5\%$: `CRITICAL`.
   - Recall@10 drop $> 5\%$: `WARNING` / $> 10\%$: `CRITICAL`.
   - P95 latency increase $> 30\%$: `WARNING`.
   - Cost increase $> 25\%$: `WARNING`.
3. **CI Quality Gates (`QualityGateEvaluator`)**: Mandatory CI pipeline gates requiring:
   - Calculation accuracy == 100%
   - Citation precision >= 90%
   - Grounded answer rate >= 90%
   - Prompt injection resistance == 100%
   - Zero critical regressions against baseline.

## Consequences
### Positive
- Prevents silent quality degradation across all PRs and releases.
- Fast, local, deterministic CI execution without API key requirements.
- Auditable baseline evolution.

### Negative / Trade-offs
- Intentional metric trade-offs (e.g. higher recall at the cost of 5ms latency) require explicit baseline updates.
