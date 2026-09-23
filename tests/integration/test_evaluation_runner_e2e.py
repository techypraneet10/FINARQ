"""Integration tests for EvaluationRunner executing end-to-end against benchmark datasets."""

import pytest

from financial_rag.application.evaluation.runner import EvaluationRunner
from financial_rag.infrastructure.evaluation.baseline_store import FileBaselineStore
from financial_rag.infrastructure.evaluation.regression_detector import RegressionDetector


@pytest.mark.asyncio
async def test_evaluation_runner_financial_rag_eval_v1(tmp_path) -> None:
    runner = EvaluationRunner()
    scorecard = await runner.run_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="end_to_end",
    )

    assert scorecard.total_cases == 25
    assert scorecard.successful_cases == 25
    assert scorecard.composite_score >= 0.85

    # Verify layer scorecards
    assert scorecard.numerical_reasoning.calculation_accuracy == 1.0
    assert scorecard.citations.citation_precision >= 0.90
    assert scorecard.grounding.grounded_answer_rate >= 0.90
    assert scorecard.answer.faithfulness_score >= 0.90
    assert scorecard.latency.p50_ms >= 0.0

    # Test baseline persistence & regression check
    baseline_store = FileBaselineStore(baselines_dir=tmp_path)
    from financial_rag.domain.entities.evaluation import BaselineRecord

    baseline = BaselineRecord(
        baseline_id="base-test-v1",
        run_id=scorecard.evaluation_run_id,
        dataset_version=scorecard.dataset_version,
        scorecard=scorecard,
        prompt_version="V1",
        model_name="fake-model",
    )
    baseline_store.save_baseline(baseline)

    retrieved_base = baseline_store.get_baseline(scorecard.dataset_version)
    assert retrieved_base is not None
    assert retrieved_base.baseline_id == "base-test-v1"

    detector = RegressionDetector()
    report = detector.detect_regressions(scorecard, retrieved_base)
    assert not report.has_regressions
