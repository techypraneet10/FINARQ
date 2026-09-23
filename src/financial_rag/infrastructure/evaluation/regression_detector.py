"""Regression detection engine comparing evaluation runs against approved baselines."""

from financial_rag.domain.entities.evaluation import (
    BaselineRecord,
    EvaluationScorecard,
    RegressionItem,
    RegressionReport,
    RegressionSeverity,
)
from financial_rag.domain.interfaces.evaluation import RegressionDetectorProtocol

DEFAULT_REGRESSION_THRESHOLDS: dict[str, float] = {
    # Absolute tolerance drops (0.0 to 1.0)
    "calculation_accuracy_drop_max": 0.00,  # Strict zero tolerance for math regression
    "citation_precision_drop_max": 0.02,
    "grounded_answer_rate_drop_max": 0.02,
    "evidence_recall_drop_max": 0.05,
    "recall_at_10_drop_max": 0.05,
    "mrr_drop_max": 0.05,
    "faithfulness_drop_max": 0.02,
    "numerical_fidelity_drop_max": 0.00,
    "prompt_injection_resistance_drop_max": 0.00,
    # Relative percentage increase tolerances
    "p95_latency_increase_max_pct": 0.30,  # 30% latency increase
    "cost_increase_max_pct": 0.25,  # 25% cost increase
}


class RegressionDetector(RegressionDetectorProtocol):
    """Detects quality and performance regressions by comparing current scorecard against baseline snapshot."""

    def __init__(self, default_thresholds: dict[str, float] | None = None) -> None:
        self.thresholds = dict(DEFAULT_REGRESSION_THRESHOLDS)
        if default_thresholds:
            self.thresholds.update(default_thresholds)

    def detect_regressions(
        self,
        current_scorecard: EvaluationScorecard,
        baseline: BaselineRecord,
        thresholds: dict[str, float] | None = None,
    ) -> RegressionReport:
        """Compare scorecard metrics against baseline values."""
        active_thresh = dict(self.thresholds)
        if thresholds:
            active_thresh.update(thresholds)

        base_sc = baseline.scorecard
        regressions: list[RegressionItem] = []

        def check_drop(
            metric_name: str,
            cur_val: float,
            base_val: float,
            threshold_key: str,
            is_critical_drop: bool = False,
        ) -> None:
            delta = cur_val - base_val
            allowed_drop = active_thresh.get(threshold_key, 0.02)
            if delta < -allowed_drop:
                severity = (
                    RegressionSeverity.CRITICAL
                    if is_critical_drop or abs(delta) > (allowed_drop * 2)
                    else RegressionSeverity.WARNING
                )
                regressions.append(
                    RegressionItem(
                        metric_name=metric_name,
                        baseline_value=round(base_val, 4),
                        current_value=round(cur_val, 4),
                        delta=round(delta, 4),
                        threshold=allowed_drop,
                        severity=severity,
                        details=f"Metric decreased by {abs(delta) * 100:.2f}% (exceeds allowed tolerance of {allowed_drop * 100:.2f}%)",
                    )
                )

        def check_increase(
            metric_name: str,
            cur_val: float,
            base_val: float,
            threshold_key: str,
            min_abs_delta: float = 5.0,
        ) -> None:
            if base_val <= 0.0:
                return
            abs_delta = cur_val - base_val
            pct_increase = abs_delta / base_val
            allowed_increase = active_thresh.get(threshold_key, 0.25)
            if pct_increase > allowed_increase and abs_delta >= min_abs_delta:
                regressions.append(
                    RegressionItem(
                        metric_name=metric_name,
                        baseline_value=round(base_val, 2),
                        current_value=round(cur_val, 2),
                        delta=round(pct_increase, 4),
                        threshold=allowed_increase,
                        severity=RegressionSeverity.WARNING,
                        details=f"Metric increased by {pct_increase * 100:.1f}% (exceeds allowed tolerance of {allowed_increase * 100:.1f}%)",
                    )
                )

        # 1. Check Retrieval Metrics
        check_drop(
            "Recall@10",
            current_scorecard.retrieval.recall_at_10,
            base_sc.retrieval.recall_at_10,
            "recall_at_10_drop_max",
        )
        check_drop("MRR", current_scorecard.retrieval.mrr, base_sc.retrieval.mrr, "mrr_drop_max")

        # 2. Check Reasoning Metrics (Zero Tolerance)
        check_drop(
            "Calculation Accuracy",
            current_scorecard.numerical_reasoning.calculation_accuracy,
            base_sc.numerical_reasoning.calculation_accuracy,
            "calculation_accuracy_drop_max",
            is_critical_drop=True,
        )

        # 3. Check Grounding & Evidence
        check_drop(
            "Citation Precision",
            current_scorecard.citations.citation_precision,
            base_sc.citations.citation_precision,
            "citation_precision_drop_max",
        )
        check_drop(
            "Evidence Recall",
            current_scorecard.evidence.evidence_recall,
            base_sc.evidence.evidence_recall,
            "evidence_recall_drop_max",
        )
        check_drop(
            "Grounded Answer Rate",
            current_scorecard.grounding.grounded_answer_rate,
            base_sc.grounding.grounded_answer_rate,
            "grounded_answer_rate_drop_max",
            is_critical_drop=True,
        )

        # 4. Check Answer Quality & Security
        check_drop(
            "Answer Faithfulness",
            current_scorecard.answer.faithfulness_score,
            base_sc.answer.faithfulness_score,
            "faithfulness_drop_max",
        )
        check_drop(
            "Numerical Fidelity",
            current_scorecard.answer.numerical_fidelity_score,
            base_sc.answer.numerical_fidelity_score,
            "numerical_fidelity_drop_max",
            is_critical_drop=True,
        )
        check_drop(
            "Prompt Injection Resistance",
            current_scorecard.security.prompt_injection_resistance_rate,
            base_sc.security.prompt_injection_resistance_rate,
            "prompt_injection_resistance_drop_max",
            is_critical_drop=True,
        )

        # 5. Check Performance & Cost Increases
        check_increase(
            "P95 Latency (ms)",
            current_scorecard.latency.p95_ms,
            base_sc.latency.p95_ms,
            "p95_latency_increase_max_pct",
        )
        check_increase(
            "Estimated Cost per Query (USD)",
            current_scorecard.cost.cost_per_query_usd,
            base_sc.cost.cost_per_query_usd,
            "cost_increase_max_pct",
        )

        return RegressionReport(
            run_id=current_scorecard.evaluation_run_id,
            baseline_id=baseline.baseline_id,
            has_regressions=len(regressions) > 0,
            regressions=regressions,
        )
