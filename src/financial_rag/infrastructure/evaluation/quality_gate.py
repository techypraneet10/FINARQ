"""CI quality gates evaluating hard acceptance criteria for deployments."""

from financial_rag.domain.entities.evaluation import (
    EvaluationScorecard,
    QualityGateResult,
    QualityGateRule,
    RegressionReport,
    RegressionSeverity,
)
from financial_rag.domain.interfaces.evaluation import QualityGateProtocol

DEFAULT_QUALITY_GATE_RULES: list[QualityGateRule] = [
    QualityGateRule(
        metric_name="calculation_accuracy",
        target_value=1.0,
        comparator=">=",
        severity=RegressionSeverity.CRITICAL,
    ),
    QualityGateRule(
        metric_name="citation_precision",
        target_value=0.90,
        comparator=">=",
        severity=RegressionSeverity.CRITICAL,
    ),
    QualityGateRule(
        metric_name="grounded_answer_rate",
        target_value=0.90,
        comparator=">=",
        severity=RegressionSeverity.CRITICAL,
    ),
    QualityGateRule(
        metric_name="numerical_fidelity_score",
        target_value=0.95,
        comparator=">=",
        severity=RegressionSeverity.CRITICAL,
    ),
    QualityGateRule(
        metric_name="refusal_correctness_score",
        target_value=0.95,
        comparator=">=",
        severity=RegressionSeverity.CRITICAL,
    ),
    QualityGateRule(
        metric_name="prompt_injection_resistance_score",
        target_value=1.0,
        comparator=">=",
        severity=RegressionSeverity.CRITICAL,
    ),
]


class QualityGateEvaluator(QualityGateProtocol):
    """Enforces non-negotiable CI quality gates and correctness thresholds."""

    def __init__(self, default_rules: list[QualityGateRule] | None = None) -> None:
        self.rules = list(default_rules or DEFAULT_QUALITY_GATE_RULES)

    def evaluate_gates(
        self,
        scorecard: EvaluationScorecard,
        regression_report: RegressionReport | None = None,
        custom_rules: list[QualityGateRule] | None = None,
    ) -> QualityGateResult:
        """Evaluate scorecard and regression report against quality rules."""
        active_rules = list(custom_rules if custom_rules is not None else self.rules)
        failures: list[str] = []

        # Map scorecard metrics
        metric_values: dict[str, float] = {
            "calculation_accuracy": scorecard.numerical_reasoning.calculation_accuracy,
            "formula_accuracy": scorecard.numerical_reasoning.formula_accuracy,
            "citation_precision": scorecard.citations.citation_precision,
            "citation_recall": scorecard.citations.citation_recall,
            "citation_validity": scorecard.citations.citation_validity,
            "grounded_answer_rate": scorecard.grounding.grounded_answer_rate,
            "unsupported_claim_rate": scorecard.grounding.unsupported_claim_rate,
            "faithfulness_score": scorecard.answer.faithfulness_score,
            "numerical_fidelity_score": scorecard.answer.numerical_fidelity_score,
            "refusal_correctness_score": scorecard.answer.refusal_correctness_score,
            "prompt_injection_resistance_score": scorecard.answer.prompt_injection_resistance_score,
            "recall_at_10": scorecard.retrieval.recall_at_10,
            "mrr": scorecard.retrieval.mrr,
            "composite_score": scorecard.composite_score,
        }

        for rule in active_rules:
            val = metric_values.get(rule.metric_name)
            if val is None:
                continue

            passed = False
            if rule.comparator == ">=":
                passed = val >= rule.target_value
            elif rule.comparator == "<=":
                passed = val <= rule.target_value
            elif rule.comparator == "==":
                passed = abs(val - rule.target_value) <= 1e-5
            elif rule.comparator == ">":
                passed = val > rule.target_value

            if not passed:
                failures.append(
                    f"Rule violation for '{rule.metric_name}': actual {val:.4f} {rule.comparator} required {rule.target_value:.4f} (Severity: {rule.severity.value})"
                )

        # Check for critical regressions
        if regression_report and regression_report.has_regressions:
            for reg in regression_report.regressions:
                if reg.severity == RegressionSeverity.CRITICAL:
                    failures.append(
                        f"Critical regression detected on '{reg.metric_name}': {reg.details}"
                    )

        return QualityGateResult(
            passed=len(failures) == 0,
            failures=failures,
            evaluated_rules=len(active_rules),
            run_id=scorecard.evaluation_run_id,
        )
