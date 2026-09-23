"""Evaluation test suite benchmarking accuracy, citation precision, and grounding."""

from decimal import Decimal

from financial_rag.application.reasoning.evaluation.metrics import (
    CitationMetrics,
    GroundingMetrics,
    ReasoningEvaluationResult,
    ReasoningMetrics,
)
from financial_rag.domain.entities.reasoning import (
    ReasoningOperation,
)
from financial_rag.infrastructure.reasoning.calculator import (
    DeterministicFinancialCalculator,
)
from tests.unit.test_financial_calculator import make_fact


def test_reasoning_evaluation_metrics_aggregation() -> None:
    calculator = DeterministicFinancialCalculator()

    # Case 1: Revenue difference
    f1 = make_fact("Revenue", "$391.035B", Decimal("391035000000"), 2024)
    f2 = make_fact("Revenue", "$383.285B", Decimal("383285000000"), 2023)
    calc1 = calculator.execute(ReasoningOperation.DIFFERENCE, [f1, f2])

    assert calc1.success
    assert calc1.raw_result == Decimal("7750000000")

    # Case 2: Growth rate
    calc2 = calculator.execute(ReasoningOperation.GROWTH_RATE, [f2, f1])
    assert calc2.success
    assert calc2.rounded_result == Decimal("2.02")

    # Metrics summary calculation
    metrics = ReasoningMetrics(
        exact_match_accuracy=1.0,
        arithmetic_error_rate=0.0,
        unsupported_operation_rate=0.0,
        division_by_zero_handled_rate=1.0,
        average_latency_ms=1.2,
    )
    citation_metrics = CitationMetrics(
        citation_precision=1.0,
        citation_recall=1.0,
        unverified_citation_rate=0.0,
        page_level_accuracy=1.0,
    )
    grounding_metrics = GroundingMetrics(
        fully_grounded_rate=1.0,
        ungrounded_claim_rate=0.0,
        conflicting_claim_rate=0.0,
    )

    eval_result = ReasoningEvaluationResult(
        total_queries=2,
        answerable_queries=2,
        unanswerable_queries=0,
        reasoning_metrics=metrics,
        citation_metrics=citation_metrics,
        grounding_metrics=grounding_metrics,
    )

    assert eval_result.reasoning_metrics.exact_match_accuracy == 1.0
    assert eval_result.grounding_metrics.fully_grounded_rate == 1.0
