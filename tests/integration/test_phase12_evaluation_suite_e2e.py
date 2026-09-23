"""End-to-end integration tests for Phase 12 Evaluation, Benchmarks, Baselines, and Quality Gates."""

import json
from pathlib import Path

import pytest

from financial_rag.application.evaluation.runner import EvaluationRunner
from financial_rag.application.evaluation.service import EvaluationService
from financial_rag.domain.entities.evaluation import (
    BaselineRecord,
    RegressionSeverity,
)
from financial_rag.infrastructure.evaluation.baseline_store import FileBaselineStore
from financial_rag.infrastructure.evaluation.quality_gate import QualityGateEvaluator
from financial_rag.infrastructure.evaluation.regression_detector import RegressionDetector
from financial_rag.infrastructure.evaluation.report_formatter import ReportFormatter


@pytest.mark.asyncio
async def test_phase12_evaluation_full_dataset_execution(tmp_path: Path) -> None:
    """Execute complete 25-case benchmark evaluation on financial_rag_eval_v1."""
    eval_service = EvaluationService(
        baseline_store=FileBaselineStore(baselines_dir=tmp_path),
    )

    scorecard, _regression_report, gate_result = await eval_service.execute_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="end_to_end",
        compare_baseline=False,
        enforce_gates=True,
    )

    # 1. Dataset & Execution Counts
    assert scorecard.dataset_version == "financial_rag_eval_v1"
    assert scorecard.total_cases == 25
    assert scorecard.successful_cases == 25
    assert scorecard.composite_score >= 0.90

    # 2. Retrieval Metrics
    assert scorecard.retrieval.recall_at_10 >= 0.85
    assert scorecard.retrieval.hit_rate_at_10 >= 0.85
    assert scorecard.retrieval.mrr >= 0.80
    assert scorecard.retrieval.map_score >= 0.80

    # 3. Deterministic Arithmetic & Fact Extraction (Zero-Tolerance)
    assert scorecard.numerical_reasoning.calculation_accuracy == 1.0
    assert scorecard.numerical_reasoning.formula_accuracy == 1.0
    assert scorecard.numerical_reasoning.zero_division_safety == 1.0
    assert scorecard.fact_extraction.exact_match == 1.0
    assert scorecard.fact_extraction.f1 == 1.0

    # 4. Citations & Evidence Grounding
    assert scorecard.citations.citation_precision >= 0.95
    assert scorecard.citations.citation_recall >= 0.95
    assert scorecard.citations.citation_validity == 1.0
    assert scorecard.citations.citation_completeness == 1.0
    assert scorecard.grounding.grounded_answer_rate == 1.0
    assert scorecard.grounding.unsupported_claim_rate == 0.0

    # 5. Answer Faithfulness, Refusals & Injection Resistance
    assert scorecard.answer.faithfulness_score >= 0.95
    assert scorecard.answer.refusal_correctness_score == 1.0
    assert scorecard.answer.prompt_injection_resistance_score == 1.0

    # 6. Quality Gates Verification
    assert gate_result.passed is True
    assert len(gate_result.failures) == 0


@pytest.mark.asyncio
async def test_phase12_baseline_persistence_and_regression_detection(tmp_path: Path) -> None:
    """Validate saving baseline snapshot and verifying that identical/improved runs show zero regressions."""
    baseline_store = FileBaselineStore(baselines_dir=tmp_path)
    eval_service = EvaluationService(baseline_store=baseline_store)

    # 1. Run and save baseline
    scorecard, _, _ = await eval_service.execute_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="end_to_end",
        compare_baseline=False,
    )
    baseline_record = eval_service.save_as_baseline(scorecard, approved_by="eval-lead")
    assert baseline_record.baseline_id == "base-financial_rag_eval_v1"

    # 2. Run second evaluation comparing against baseline
    _scorecard_2, regression_2, gate_2 = await eval_service.execute_evaluation(
        dataset_version="financial_rag_eval_v1",
        suite="end_to_end",
        compare_baseline=True,
    )

    assert regression_2 is not None
    assert regression_2.has_regressions is False
    assert len(regression_2.regressions) == 0
    assert gate_2.passed is True


@pytest.mark.asyncio
async def test_phase12_regression_detector_catches_degraded_math() -> None:
    """Verify regression detector raises CRITICAL regression on mathematical accuracy drop."""
    runner = EvaluationRunner()

    scorecard = await runner.run_evaluation(dataset_version="financial_rag_eval_v1")

    # Baseline with 100% calculation accuracy
    baseline = BaselineRecord(
        baseline_id="base-gold",
        run_id="run-gold",
        dataset_version="financial_rag_eval_v1",
        scorecard=scorecard,
        prompt_version="V1",
        model_name="fake-model",
    )

    # Simulate candidate scorecard with degraded math (95% instead of 100%)
    degraded_scorecard = await runner.run_evaluation(dataset_version="financial_rag_eval_v1")
    degraded_scorecard.numerical_reasoning.calculation_accuracy = 0.95

    detector = RegressionDetector()
    report = detector.detect_regressions(degraded_scorecard, baseline)

    assert report.has_regressions is True
    math_reg = next(
        (r for r in report.regressions if r.metric_name == "Calculation Accuracy"), None
    )
    assert math_reg is not None
    assert math_reg.severity == RegressionSeverity.CRITICAL

    # Check that quality gate evaluator also catches this critical regression
    gate_evaluator = QualityGateEvaluator()
    gate_result = gate_evaluator.evaluate_gates(degraded_scorecard, report)
    assert gate_result.passed is False
    assert any(
        "Calculation Accuracy" in f or "calculation_accuracy" in f for f in gate_result.failures
    )


@pytest.mark.asyncio
async def test_phase12_retrieval_ablation_study() -> None:
    """Verify retrieval ablation matrix returns comparative metrics across strategies."""
    eval_service = EvaluationService()
    ablation = await eval_service.run_retrieval_ablation(dataset_version="financial_rag_eval_v1")

    assert "dense_only" in ablation
    assert "sparse_only" in ablation
    assert "hybrid" in ablation
    assert "hybrid_rerank" in ablation

    for _strat, met in ablation.items():
        assert met.recall_at_10 >= 0.0
        assert met.hit_rate_at_10 >= 0.0
        assert met.mrr >= 0.0
        assert met.map_score >= 0.0


@pytest.mark.asyncio
async def test_phase12_report_formatter_multi_format() -> None:
    """Verify report formatting across Markdown, JSON, and CSV."""
    runner = EvaluationRunner()
    scorecard = await runner.run_evaluation(dataset_version="financial_rag_eval_v1")

    formatter = ReportFormatter()

    # Markdown
    md = formatter.format_markdown(scorecard)
    assert "# Financial RAG Evaluation Scorecard" in md
    assert "Retrieval" in md
    assert "Calculation Accuracy" in md
    assert "Grounded Answer Rate" in md
    assert "MAP" in md

    # JSON
    js = formatter.format_json(scorecard)
    parsed = json.loads(js)
    assert parsed["dataset_version"] == "financial_rag_eval_v1"
    assert "retrieval" in parsed["metrics"]
    assert "numerical_reasoning" in parsed["metrics"]

    # CSV
    csv_out = formatter.format_csv(scorecard)
    assert "Metric Group,Metric Name,Value" in csv_out
    assert "Calculation Accuracy" in csv_out
    assert "Retrieval,MAP" in csv_out
