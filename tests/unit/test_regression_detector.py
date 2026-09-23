"""Unit tests for regression detection and threshold triggers."""

from financial_rag.domain.entities.evaluation import (
    AnswerEvalMetrics,
    BaselineRecord,
    CitationEvalMetrics,
    CostEvalMetrics,
    EvaluationScorecard,
    FactExtractionEvalMetrics,
    GroundingEvalMetrics,
    LatencyEvalMetrics,
    NumericalReasoningEvalMetrics,
    RegressionSeverity,
    RetrievalEvalMetrics,
)
from financial_rag.infrastructure.evaluation.regression_detector import RegressionDetector


def make_sample_scorecard(
    calc_acc: float = 1.0, recall: float = 0.95, p95_lat: float = 100.0
) -> EvaluationScorecard:
    return EvaluationScorecard(
        evaluation_run_id="run-test",
        dataset_version="v1",
        total_cases=10,
        successful_cases=10,
        retrieval=RetrievalEvalMetrics(recall_at_10=recall, mrr=0.85),
        fact_extraction=FactExtractionEvalMetrics(f1=0.95),
        numerical_reasoning=NumericalReasoningEvalMetrics(calculation_accuracy=calc_acc),
        citations=CitationEvalMetrics(citation_precision=0.98),
        grounding=GroundingEvalMetrics(grounded_answer_rate=0.98),
        answer=AnswerEvalMetrics(faithfulness_score=0.98, numerical_fidelity_score=1.0),
        latency=LatencyEvalMetrics(p95_ms=p95_lat),
        cost=CostEvalMetrics(cost_per_query_usd=0.001),
        composite_score=0.97,
    )


def test_regression_detector_no_regression() -> None:
    detector = RegressionDetector()
    scorecard = make_sample_scorecard()
    baseline = BaselineRecord(
        baseline_id="base-v1",
        run_id="run-base",
        dataset_version="v1",
        scorecard=scorecard,
        prompt_version="V1",
        model_name="fake",
    )

    report = detector.detect_regressions(scorecard, baseline)
    assert not report.has_regressions
    assert len(report.regressions) == 0


def test_regression_detector_critical_math_regression() -> None:
    detector = RegressionDetector()
    base_sc = make_sample_scorecard(calc_acc=1.0)
    current_sc = make_sample_scorecard(calc_acc=0.90)  # Dropped from 100% to 90%

    baseline = BaselineRecord(
        baseline_id="base-v1",
        run_id="run-base",
        dataset_version="v1",
        scorecard=base_sc,
        prompt_version="V1",
        model_name="fake",
    )

    report = detector.detect_regressions(current_sc, baseline)
    assert report.has_regressions
    assert len(report.regressions) >= 1

    math_reg = next(r for r in report.regressions if r.metric_name == "Calculation Accuracy")
    assert math_reg.severity == RegressionSeverity.CRITICAL


def test_regression_detector_latency_regression() -> None:
    detector = RegressionDetector()
    base_sc = make_sample_scorecard(p95_lat=100.0)
    current_sc = make_sample_scorecard(p95_lat=180.0)  # 80% latency increase (>30% tolerance)

    baseline = BaselineRecord(
        baseline_id="base-v1",
        run_id="run-base",
        dataset_version="v1",
        scorecard=base_sc,
        prompt_version="V1",
        model_name="fake",
    )

    report = detector.detect_regressions(current_sc, baseline)
    assert report.has_regressions
    lat_reg = next(r for r in report.regressions if "Latency" in r.metric_name)
    assert lat_reg.severity == RegressionSeverity.WARNING
