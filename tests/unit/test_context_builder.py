"""Unit tests for DeterministicContextBuilder."""

from decimal import Decimal

from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    CalculationResult,
    Citation,
    CitationType,
    Claim,
    FinancialFact,
    FinancialScale,
    FinancialValue,
    FiscalPeriod,
    GroundingStatus,
    GroundingValidationResult,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.infrastructure.llm.context_builder import DeterministicContextBuilder


def make_test_answer_package() -> AnswerPackage:
    val = FinancialValue(
        raw_value="391,035",
        display_value="$391,035 million",
        numeric_value=Decimal("391035000000"),
        unscaled_value=Decimal("391035"),
        currency="USD",
        scale=FinancialScale.MILLIONS,
        unit="USD",
    )
    period = FiscalPeriod(
        fiscal_year=2024,
        period_type="FY",
        source_text="2024",
    )

    fact = FinancialFact(
        fact_id="fact-1",
        metric="Total net sales",
        value=val,
        period=period,
        company="Apple Inc.",
        ticker="AAPL",
        document_id="doc-10k-2024",
        document_version_id="ver-1",
        page_number=45,
        chunk_id="chunk-1",
        table_id="tbl-1",
        source_evidence_id="ev-1",
        extraction_method="table_structured",
        confidence=0.98,
        source_text="Total net sales | 391,035",
    )
    calc = CalculationResult(
        calculation_id="calc-1",
        operation=ReasoningOperation.GROWTH_RATE,
        formula="((391035 - 383285) / 383285) * 100",
        inputs=[],
        input_fact_ids=["fact-1"],
        raw_result=Decimal("2.022"),
        rounded_result=Decimal("2.02"),
        display_result="+2.02%",
        unit="%",
        currency=None,
        success=True,
    )

    claim = Claim(
        claim_id="claim-1",
        text="Total net sales increased by +2.02% in FY2024.",
        claim_type="calculated",
        source_fact_ids=["fact-1"],
        calculation_ids=["calc-1"],
        reasoning_step_ids=[1],
        confidence=0.95,
        is_grounded=True,
    )

    cit = Citation(
        citation_id="cit-1",
        claim_id="claim-1",
        document_id="doc-10k-2024",
        document_version_id="ver-1",
        page_number=45,
        page_numbers=[45],
        chunk_id="chunk-1",
        table_id=None,
        section_path="Item 8 > Financial Statements",
        ticker="AAPL",
        source_excerpt="Total net sales: 391,035",
        bounding_box=None,
        citation_type=CitationType.TABLE_CELL,
        verified=True,
    )

    plan = ReasoningPlan(
        plan_id="plan-1",
        query="What was Apple's revenue growth in 2024?",
        operations=[ReasoningOperation.GROWTH_RATE],
        target_metrics=["Total net sales"],
        target_periods=["2024"],
        target_companies=["AAPL"],
        required_fact_keys=["revenue_2024"],
        steps_description=["Calculate growth"],
    )
    grounding = GroundingValidationResult(
        status=GroundingStatus.GROUNDED,
        total_claims=1,
        grounded_claims=1,
        ungrounded_claims=0,
        conflicting_claims=0,
        unverified_citations=0,
    )

    return AnswerPackage(
        package_id="pkg-123",
        query_id="q-123",
        raw_query="What was Apple's revenue growth in 2024?",
        normalized_query="What was Apple's revenue growth in 2024?",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="All required facts available.",
        reasoning_plan=plan,
        facts=[fact],
        calculations=[calc],
        reasoning_trace=[],
        claims=[claim],
        citations=[cit],
        evidence=[],
        grounding_validation=grounding,
        confidence_score=0.98,
    )


def test_context_builder_sections() -> None:
    builder = DeterministicContextBuilder()
    pkg = make_test_answer_package()
    context = builder.build_context(pkg, max_tokens=2000)

    assert "<QUESTION>" in context
    assert "<ANSWERABILITY>" in context
    assert "<VERIFIED_FACTS>" in context
    assert "<CALCULATIONS>" in context
    assert "<CLAIMS>" in context
    assert "<CITATION_MAP>" in context
    assert "[C1] -> ID: cit-1" in context
    assert "$391,035 million" in context
    assert "+2.02%" in context


def test_context_builder_budget_truncation() -> None:
    builder = DeterministicContextBuilder()
    pkg = make_test_answer_package()
    # Very small token budget
    context = builder.build_context(pkg, max_tokens=50)
    assert len(context) <= 300
