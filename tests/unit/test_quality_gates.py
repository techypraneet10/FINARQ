"""Unit tests for CI quality gates enforcement."""

from financial_rag.domain.entities.evaluation import (
    RegressionItem,
    RegressionReport,
    RegressionSeverity,
)
from financial_rag.infrastructure.evaluation.quality_gate import QualityGateEvaluator
from tests.unit.test_regression_detector import make_sample_scorecard


def test_quality_gates_pass() -> None:
    evaluator = QualityGateEvaluator()
    scorecard = make_sample_scorecard(calc_acc=1.0)
    result = evaluator.evaluate_gates(scorecard)

    assert result.passed
    assert len(result.failures) == 0


def test_quality_gates_fail_on_math_inaccuracy() -> None:
    evaluator = QualityGateEvaluator()
    scorecard = make_sample_scorecard(calc_acc=0.98)  # Requires 1.0
    result = evaluator.evaluate_gates(scorecard)

    assert not result.passed
    assert any("calculation_accuracy" in f for f in result.failures)


def test_quality_gates_fail_on_critical_regression() -> None:
    evaluator = QualityGateEvaluator()
    scorecard = make_sample_scorecard(calc_acc=1.0)
    regression_report = RegressionReport(
        run_id="run-1",
        baseline_id="base-1",
        has_regressions=True,
        regressions=[
            RegressionItem(
                metric_name="Grounded Answer Rate",
                baseline_value=1.0,
                current_value=0.85,
                delta=-0.15,
                threshold=0.02,
                severity=RegressionSeverity.CRITICAL,
                details="Grounding dropped by 15%",
            )
        ],
    )

    result = evaluator.evaluate_gates(scorecard, regression_report)
    assert not result.passed
    assert any("Critical regression" in f for f in result.failures)
