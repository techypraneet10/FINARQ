"""Regression test suite guarding against historical regressions and mathematical divergence."""

import pytest

from financial_rag.application.evaluation.service import EvaluationService


@pytest.mark.asyncio
async def test_known_regressions_against_baseline(tmp_path) -> None:
    eval_service = EvaluationService()

    # 1. Run baseline evaluation
    scorecard, _, _ = await eval_service.execute_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="all",
        compare_baseline=False,
    )

    # 2. Persist baseline
    eval_service.save_as_baseline(scorecard, approved_by="ci-engineer")

    # 3. Run regression check
    _, regression_report, gate_result = await eval_service.execute_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="all",
        compare_baseline=True,
        enforce_gates=True,
    )

    assert regression_report is not None
    assert not regression_report.has_regressions
    assert gate_result.passed
