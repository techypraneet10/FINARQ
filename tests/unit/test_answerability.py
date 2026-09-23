"""Unit tests for answerability state evaluation machine."""

from decimal import Decimal

import pytest

from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    CalculationResult,
    EvidenceConflict,
    GroundingStatus,
    GroundingValidationResult,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.infrastructure.reasoning.answerability import (
    DeterministicAnswerabilityEvaluator,
)
from tests.unit.test_financial_calculator import make_fact


@pytest.fixture
def evaluator() -> DeterministicAnswerabilityEvaluator:
    return DeterministicAnswerabilityEvaluator()


def test_answerable_evaluation(evaluator: DeterministicAnswerabilityEvaluator) -> None:
    f1 = make_fact("Revenue", "$391.035B", Decimal("391035000000"), 2024)
    plan = ReasoningPlan(
        plan_id="plan-1",
        query="What was revenue in 2024?",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=["Revenue"],
        target_periods=["2024"],
        target_companies=["AAPL"],
        required_fact_keys=["revenue_2024"],
        steps_description=["Direct lookup"],
    )
    grounding = GroundingValidationResult(
        status=GroundingStatus.GROUNDED,
        total_claims=1,
        grounded_claims=1,
        ungrounded_claims=0,
        conflicting_claims=0,
        unverified_citations=0,
    )

    status, _rationale, missing = evaluator.evaluate(plan, [f1], [], [], grounding)
    assert status == AnswerabilityStatus.ANSWERABLE
    assert len(missing) == 0


def test_insufficient_evidence_when_no_facts_extracted(
    evaluator: DeterministicAnswerabilityEvaluator,
) -> None:
    plan = ReasoningPlan(
        plan_id="plan-2",
        query="What was revenue in 2030?",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=["Revenue"],
        target_periods=["2030"],
        target_companies=["AAPL"],
        required_fact_keys=["revenue_2030"],
        steps_description=["Direct lookup"],
    )
    grounding = GroundingValidationResult(
        status=GroundingStatus.GROUNDED,
        total_claims=0,
        grounded_claims=0,
        ungrounded_claims=0,
        conflicting_claims=0,
        unverified_citations=0,
    )

    status, _rationale, missing = evaluator.evaluate(plan, [], [], [], grounding)
    assert status == AnswerabilityStatus.INSUFFICIENT_EVIDENCE
    assert "revenue_2030" in missing


def test_calculation_failed_evaluation(
    evaluator: DeterministicAnswerabilityEvaluator,
) -> None:
    f1 = make_fact("Revenue", "$0", Decimal("0"), 2023)
    f2 = make_fact("Revenue", "$100", Decimal("100"), 2024)
    plan = ReasoningPlan(
        plan_id="plan-3",
        query="What was revenue growth from 2023 to 2024?",
        operations=[ReasoningOperation.GROWTH_RATE],
        target_metrics=["Revenue"],
        target_periods=["2023", "2024"],
        target_companies=["AAPL"],
        required_fact_keys=["revenue_2023", "revenue_2024"],
        steps_description=["Growth rate"],
    )
    failed_calc = CalculationResult(
        calculation_id="calc-div-zero",
        operation=ReasoningOperation.GROWTH_RATE,
        formula="((100 - 0) / 0) * 100",
        inputs=[],
        input_fact_ids=[f1.fact_id, f2.fact_id],
        raw_result=Decimal("0"),
        rounded_result=Decimal("0"),
        display_result="Division by Zero",
        unit="%",
        currency=None,
        success=False,
        error_message="Division by zero: initial value is 0",
    )
    grounding = GroundingValidationResult(
        status=GroundingStatus.GROUNDED,
        total_claims=0,
        grounded_claims=0,
        ungrounded_claims=0,
        conflicting_claims=0,
        unverified_citations=0,
    )

    status, rationale, _missing = evaluator.evaluate(plan, [f1, f2], [failed_calc], [], grounding)
    assert status == AnswerabilityStatus.CALCULATION_FAILED
    assert "division by zero" in rationale.lower()


def test_conflicting_evidence_evaluation(
    evaluator: DeterministicAnswerabilityEvaluator,
) -> None:
    f1 = make_fact("Revenue", "$100", Decimal("100"), 2024)
    f2 = make_fact("Revenue", "$90", Decimal("90"), 2024)
    plan = ReasoningPlan(
        plan_id="plan-4",
        query="What was revenue in 2024?",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=["Revenue"],
        target_periods=["2024"],
        target_companies=["AAPL"],
        required_fact_keys=["revenue_2024"],
        steps_description=["Direct lookup"],
    )
    conflict = EvidenceConflict(
        conflict_id="conf-1",
        metric="Revenue",
        period="FY2024",
        conflicting_facts=[f1, f2],
        difference_description="Discrepancy: $100 vs $90",
        resolved=False,  # Unresolved
    )
    grounding = GroundingValidationResult(
        status=GroundingStatus.CONFLICTING,
        total_claims=1,
        grounded_claims=1,
        ungrounded_claims=0,
        conflicting_claims=1,
        unverified_citations=0,
    )

    status, _rationale, _missing = evaluator.evaluate(plan, [f1, f2], [], [conflict], grounding)
    assert status == AnswerabilityStatus.CONFLICTING_EVIDENCE
