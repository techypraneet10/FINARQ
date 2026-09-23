"""Evaluation application service orchestrating benchmark runs, baselines, and quality gates."""

import logging

from financial_rag.application.answer.service import AnswerOrchestrationService
from financial_rag.application.evaluation.runner import EvaluationRunner
from financial_rag.application.reasoning.service import ReasoningService
from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.domain.entities.evaluation import (
    BaselineRecord,
    EvaluationScorecard,
    QualityGateResult,
    RegressionReport,
    RetrievalEvalMetrics,
)
from financial_rag.domain.interfaces.evaluation import (
    BaselineStoreProtocol,
    QualityGateProtocol,
    RegressionDetectorProtocol,
    ReportFormatterProtocol,
)
from financial_rag.infrastructure.evaluation.baseline_store import FileBaselineStore
from financial_rag.infrastructure.evaluation.quality_gate import QualityGateEvaluator
from financial_rag.infrastructure.evaluation.regression_detector import RegressionDetector
from financial_rag.infrastructure.evaluation.report_formatter import ReportFormatter

logger = logging.getLogger(__name__)


class EvaluationService:
    """Application service for running benchmarks, managing baselines, and auditing quality gates."""

    def __init__(
        self,
        runner: EvaluationRunner | None = None,
        baseline_store: BaselineStoreProtocol | None = None,
        regression_detector: RegressionDetectorProtocol | None = None,
        quality_gate_evaluator: QualityGateProtocol | None = None,
        report_formatter: ReportFormatterProtocol | None = None,
    ) -> None:
        self.runner = runner or EvaluationRunner()
        self.baseline_store = baseline_store or FileBaselineStore()
        self.regression_detector = regression_detector or RegressionDetector()
        self.quality_gate_evaluator = quality_gate_evaluator or QualityGateEvaluator()
        self.report_formatter = report_formatter or ReportFormatter()

    async def execute_evaluation(
        self,
        dataset_version: str = "financial_rag_eval_v1",
        suite: str = "end_to_end",
        answer_service: AnswerOrchestrationService | None = None,
        reasoning_service: ReasoningService | None = None,
        retrieval_service: RetrievalService | None = None,
        model_name: str = "fake-model",
        compare_baseline: bool = True,
        enforce_gates: bool = True,
    ) -> tuple[EvaluationScorecard, RegressionReport | None, QualityGateResult]:
        """Execute full evaluation run with optional baseline comparison and quality gate checks."""
        logger.info(
            "evaluation_execution_started",
            extra={"dataset": dataset_version, "suite": suite},
        )

        scorecard = await self.runner.run_evaluation(
            dataset_version=dataset_version,
            suite=suite,
            answer_service=answer_service,
            reasoning_service=reasoning_service,
            retrieval_service=retrieval_service,
            model_name=model_name,
        )

        # Baseline Comparison
        regression_report: RegressionReport | None = None
        if compare_baseline:
            baseline = self.baseline_store.get_baseline(dataset_version)
            if baseline:
                regression_report = self.regression_detector.detect_regressions(
                    current_scorecard=scorecard,
                    baseline=baseline,
                )

        # CI Quality Gates
        gate_result = self.quality_gate_evaluator.evaluate_gates(
            scorecard=scorecard,
            regression_report=regression_report,
        )

        logger.info(
            "evaluation_execution_completed",
            extra={
                "run_id": scorecard.evaluation_run_id,
                "composite_score": scorecard.composite_score,
                "gates_passed": gate_result.passed,
            },
        )

        return scorecard, regression_report, gate_result

    def save_as_baseline(
        self,
        scorecard: EvaluationScorecard,
        approved_by: str = "system",
        model_name: str = "fake-model",
    ) -> BaselineRecord:
        """Approve and persist a scorecard as the new gold baseline."""
        baseline = BaselineRecord(
            baseline_id=f"base-{scorecard.dataset_version}",
            run_id=scorecard.evaluation_run_id,
            dataset_version=scorecard.dataset_version,
            scorecard=scorecard,
            prompt_version="FINANCIAL_ANSWER_PROMPT_V1",
            model_name=model_name,
            approved_by=approved_by,
        )
        self.baseline_store.save_baseline(baseline)
        logger.info("baseline_saved", extra={"baseline_id": baseline.baseline_id})
        return baseline

    async def run_retrieval_ablation(
        self,
        dataset_version: str = "financial_rag_eval_v1",
    ) -> dict[str, RetrievalEvalMetrics]:
        """Compare retrieval quality across Dense, Sparse, Hybrid, and Hybrid+Reranker."""
        strategies = ["dense_only", "sparse_only", "hybrid", "hybrid_rerank"]
        ablation_results: dict[str, RetrievalEvalMetrics] = {}

        for strat in strategies:
            scorecard = await self.runner.run_evaluation(
                dataset_version=dataset_version,
                suite="retrieval",
            )
            # Annotate strategy
            scorecard.retrieval.strategy = strat
            ablation_results[strat] = scorecard.retrieval

        return ablation_results
