"""Golden benchmark dataset evaluation test suite verifying all 25 test cases."""

import pytest

from financial_rag.application.evaluation.runner import EvaluationRunner
from financial_rag.infrastructure.evaluation.quality_gate import QualityGateEvaluator


@pytest.mark.asyncio
async def test_golden_dataset_v1_quality_gates() -> None:
    runner = EvaluationRunner()
    scorecard = await runner.run_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="all",
    )

    # 1. Verify 25 cases processed
    assert scorecard.total_cases == 25
    assert scorecard.successful_cases == 25

    # 2. Verify CI quality gates pass
    gate_evaluator = QualityGateEvaluator()
    gate_result = gate_evaluator.evaluate_gates(scorecard)

    assert gate_result.passed, f"Quality gate failures: {gate_result.failures}"
    assert scorecard.numerical_reasoning.calculation_accuracy == 1.0
    assert scorecard.citations.citation_precision >= 0.90
    assert scorecard.grounding.grounded_answer_rate >= 0.90
    assert scorecard.answer.prompt_injection_resistance_score == 1.0
