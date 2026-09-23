"""Unit tests for grounding validation audit engine."""

from decimal import Decimal

import pytest

from financial_rag.domain.entities.reasoning import (
    CalculationResult,
    Citation,
    CitationType,
    Claim,
    GroundingStatus,
    ReasoningOperation,
)
from financial_rag.infrastructure.reasoning.grounding_validator import (
    DeterministicGroundingValidator,
)
from tests.unit.test_financial_calculator import make_fact


@pytest.fixture
def grounding_validator() -> DeterministicGroundingValidator:
    return DeterministicGroundingValidator()


def test_fully_grounded_validation(
    grounding_validator: DeterministicGroundingValidator,
) -> None:
    f1 = make_fact("Revenue", "$100", Decimal("100"), 2024)
    claim = Claim(
        claim_id="claim-1",
        text="Revenue was $100 in 2024.",
        claim_type="direct_fact",
        source_fact_ids=[f1.fact_id],
        calculation_ids=[],
        reasoning_step_ids=[1],
        confidence=1.0,
        is_grounded=True,
    )
    citation = Citation(
        citation_id="cit-1",
        claim_id="claim-1",
        document_id=f1.document_id,
        document_version_id=f1.document_version_id,
        page_number=f1.page_number,
        page_numbers=[f1.page_number],
        chunk_id=f1.chunk_id,
        table_id=None,
        section_path="",
        ticker="AAPL",
        source_excerpt="Revenue was $100",
        bounding_box=None,
        citation_type=CitationType.DIRECT_SOURCE,
        verified=True,
    )

    res = grounding_validator.validate([claim], [f1], [], [citation], [])
    assert res.status == GroundingStatus.GROUNDED
    assert res.validation_passed
    assert res.grounded_claims == 1
    assert res.ungrounded_claims == 0


def test_ungrounded_due_to_unverified_citation(
    grounding_validator: DeterministicGroundingValidator,
) -> None:
    f1 = make_fact("Revenue", "$100", Decimal("100"), 2024)
    claim = Claim(
        claim_id="claim-1",
        text="Revenue was $100 in 2024.",
        claim_type="direct_fact",
        source_fact_ids=[f1.fact_id],
        calculation_ids=[],
        reasoning_step_ids=[1],
        confidence=1.0,
        is_grounded=True,
    )
    unverified_cit = Citation(
        citation_id="cit-1",
        claim_id="claim-1",
        document_id=f1.document_id,
        document_version_id=f1.document_version_id,
        page_number=f1.page_number,
        page_numbers=[f1.page_number],
        chunk_id=f1.chunk_id,
        table_id=None,
        section_path="",
        ticker="AAPL",
        source_excerpt="Revenue was $100",
        bounding_box=None,
        citation_type=CitationType.DIRECT_SOURCE,
        verified=False,  # Unverified
    )

    res = grounding_validator.validate([claim], [f1], [], [unverified_cit], [])
    assert res.status == GroundingStatus.UNGROUNDED
    assert not res.validation_passed
    assert res.ungrounded_claims == 1


def test_calculated_claim_failed_calculation(
    grounding_validator: DeterministicGroundingValidator,
) -> None:
    f1 = make_fact("Revenue", "$0", Decimal("0"), 2023)
    f2 = make_fact("Revenue", "$100", Decimal("100"), 2024)

    failed_calc = CalculationResult(
        calculation_id="calc-fail",
        operation=ReasoningOperation.PERCENTAGE_CHANGE,
        formula="division by zero",
        inputs=[],
        input_fact_ids=[f1.fact_id, f2.fact_id],
        raw_result=Decimal("0"),
        rounded_result=Decimal("0"),
        display_result="Failed",
        unit="%",
        currency=None,
        success=False,
        error_message="Division by zero",
    )

    claim = Claim(
        claim_id="claim-calc-1",
        text="Revenue increased by 20%",
        claim_type="calculated",
        source_fact_ids=[f1.fact_id, f2.fact_id],
        calculation_ids=["calc-fail"],
        reasoning_step_ids=[2],
        confidence=1.0,
    )

    res = grounding_validator.validate([claim], [f1, f2], [failed_calc], [], [])
    assert res.status == GroundingStatus.UNGROUNDED
    assert res.ungrounded_claims == 1
