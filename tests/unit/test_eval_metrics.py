"""Unit tests for mathematical correctness of retrieval, reasoning, citation, and grounding evaluation metrics."""

from decimal import Decimal

from financial_rag.domain.entities.evaluation import (
    EvaluationCase,
    EvaluationCategory,
    ExpectedCalculation,
    ExpectedFact,
)
from financial_rag.domain.entities.models import DocumentChunk, RetrievalResult
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
from financial_rag.infrastructure.evaluation.citation_evaluator import CitationEvaluator
from financial_rag.infrastructure.evaluation.grounding_evaluator import GroundingEvaluator
from financial_rag.infrastructure.evaluation.reasoning_evaluator import ReasoningEvaluator
from financial_rag.infrastructure.evaluation.retrieval_evaluator import RetrievalEvaluator


def test_retrieval_metrics_perfect_hit() -> None:
    evaluator = RetrievalEvaluator()
    candidates = [
        RetrievalResult(
            chunk=DocumentChunk(
                id="c-1", document_id="doc-1", page_number=45, content="text", chunk_index=0
            ),
            score=1.0,
            retrieval_method="hybrid",
        ),
        RetrievalResult(
            chunk=DocumentChunk(
                id="c-2", document_id="doc-1", page_number=46, content="text", chunk_index=1
            ),
            score=0.9,
            retrieval_method="hybrid",
        ),
    ]

    metrics = evaluator.evaluate_retrieval(
        retrieved_items=candidates,
        ground_truth_chunks=["c-1"],
        ground_truth_pages=[45],
    )

    assert metrics.hit_rate_at_1 == 1.0
    assert metrics.recall_at_1 == 1.0
    assert metrics.precision_at_1 == 1.0
    assert metrics.mrr == 1.0
    assert metrics.ndcg_at_5 == 1.0


def test_retrieval_metrics_miss() -> None:
    evaluator = RetrievalEvaluator()
    candidates = [
        RetrievalResult(
            chunk=DocumentChunk(
                id="c-other", document_id="doc-1", page_number=10, content="text", chunk_index=0
            ),
            score=1.0,
            retrieval_method="hybrid",
        ),
    ]

    metrics = evaluator.evaluate_retrieval(
        retrieved_items=candidates,
        ground_truth_chunks=["c-target"],
        ground_truth_pages=[45],
    )

    assert metrics.hit_rate_at_1 == 0.0
    assert metrics.recall_at_10 == 0.0
    assert metrics.mrr == 0.0
    assert metrics.ndcg_at_10 == 0.0


def test_reasoning_evaluator_fact_matching() -> None:
    evaluator = ReasoningEvaluator()
    case = EvaluationCase(
        case_id="case-1",
        category=EvaluationCategory.NUMERICAL_REASONING,
        query="What was Apple's total net sales in 2024?",
        expected_facts=[
            ExpectedFact(
                metric="Total net sales",
                company="Apple",
                fiscal_year=2024,
                expected_value="391035",
                scale="MILLIONS",
            )
        ],
    )

    fact = FinancialFact(
        fact_id="fact-1",
        metric="Total net sales",
        company="Apple",
        ticker="AAPL",
        period=FiscalPeriod(fiscal_year=2024, period_type="FY", source_text="2024"),
        value=FinancialValue(
            raw_value="391,035",
            display_value="$391,035 million",
            unscaled_value=Decimal("391035"),
            numeric_value=Decimal("391035000000"),
            scale=FinancialScale.MILLIONS,
        ),
        document_id="doc-1",
        document_version_id="v-1",
        page_number=45,
        chunk_id="c-1",
        table_id=None,
        source_evidence_id="ev-1",
        extraction_method="table_cell",
        confidence=1.0,
        source_text="Total net sales: $391,035",
    )

    plan = ReasoningPlan(
        plan_id="plan-1",
        query="query",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=["Total net sales"],
        target_periods=["FY2024"],
        target_companies=["Apple"],
        required_fact_keys=["Total net sales"],
        steps_description=[],
    )

    pkg = AnswerPackage(
        package_id="pkg-1",
        query_id="q-1",
        raw_query="query",
        normalized_query="query",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="Found fact",
        reasoning_plan=plan,
        facts=[fact],
        calculations=[],
        reasoning_trace=[],
        claims=[],
        citations=[],
        evidence=[],
    )

    fact_metrics = evaluator.evaluate_fact_extraction(pkg, case)
    assert fact_metrics.precision == 1.0
    assert fact_metrics.recall == 1.0
    assert fact_metrics.f1 == 1.0
    assert fact_metrics.value_accuracy == 1.0
    assert fact_metrics.period_accuracy == 1.0


def test_reasoning_evaluator_calculation_accuracy() -> None:
    evaluator = ReasoningEvaluator()
    case = EvaluationCase(
        case_id="case-2",
        category=EvaluationCategory.NUMERICAL_REASONING,
        query="Growth rate",
        expected_calculations=[
            ExpectedCalculation(
                operation=ReasoningOperation.GROWTH_RATE,
                expected_result_str="2.02",
                tolerance_pct=0.01,
            )
        ],
    )

    calc = CalculationResult(
        calculation_id="calc-1",
        operation=ReasoningOperation.GROWTH_RATE,
        formula="((391035 - 383285) / 383285) * 100",
        inputs=[],
        input_fact_ids=[],
        raw_result=Decimal("2.021967"),
        rounded_result=Decimal("2.02"),
        display_result="+2.02%",
        unit="%",
        currency="USD",
        success=True,
    )

    plan = ReasoningPlan(
        plan_id="plan-1",
        query="query",
        operations=[ReasoningOperation.GROWTH_RATE],
        target_metrics=[],
        target_periods=[],
        target_companies=[],
        required_fact_keys=[],
        steps_description=[],
    )

    pkg = AnswerPackage(
        package_id="pkg-1",
        query_id="q-1",
        raw_query="query",
        normalized_query="query",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="Calculation complete",
        reasoning_plan=plan,
        facts=[],
        calculations=[calc],
        reasoning_trace=[],
        claims=[],
        citations=[],
        evidence=[],
    )

    calc_metrics = evaluator.evaluate_numerical_reasoning(pkg, case)
    assert calc_metrics.calculation_accuracy == 1.0
    assert calc_metrics.rounding_accuracy == 1.0


def test_citation_evaluator_precision_and_recall() -> None:
    evaluator = CitationEvaluator()
    case = EvaluationCase(
        case_id="case-cit",
        category=EvaluationCategory.CITATION,
        query="Citations test",
        expected_document_ids=["doc-apple-2024"],
        expected_page_numbers=[45],
        expected_citations_count=1,
    )

    cit = Citation(
        citation_id="cit-1",
        claim_id="cl-1",
        document_id="doc-apple-2024",
        document_version_id="v1",
        page_number=45,
        page_numbers=[45],
        chunk_id="chunk-1",
        table_id=None,
        section_path="Item 8",
        ticker="AAPL",
        source_excerpt="Total net sales $391,035",
        bounding_box=None,
        citation_type=CitationType.TABLE_CELL,
        verified=True,
    )

    plan = ReasoningPlan(
        plan_id="plan-1",
        query="query",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=[],
        target_periods=[],
        target_companies=[],
        required_fact_keys=[],
        steps_description=[],
    )

    pkg = AnswerPackage(
        package_id="pkg-1",
        query_id="q-1",
        raw_query="query",
        normalized_query="query",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="Verified citations",
        reasoning_plan=plan,
        facts=[],
        calculations=[],
        reasoning_trace=[],
        citations=[cit],
        claims=[
            Claim(
                claim_id="cl-1",
                text="Revenue was $391,035M",
                claim_type="direct_fact",
                source_fact_ids=[],
                calculation_ids=[],
                reasoning_step_ids=[1],
                is_grounded=True,
            )
        ],
        evidence=[],
    )

    cit_metrics = evaluator.evaluate_citations(pkg, case)
    assert cit_metrics.citation_precision == 1.0
    assert cit_metrics.citation_recall == 1.0
    assert cit_metrics.citation_validity == 1.0
    assert cit_metrics.citation_completeness == 1.0


def test_grounding_evaluator_rates() -> None:
    evaluator = GroundingEvaluator()
    case = EvaluationCase(
        case_id="case-grd",
        category=EvaluationCategory.GROUNDING,
        query="Grounding test",
        expected_grounding_status=GroundingStatus.GROUNDED,
    )

    plan = ReasoningPlan(
        plan_id="plan-1",
        query="query",
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=[],
        target_periods=[],
        target_companies=[],
        required_fact_keys=[],
        steps_description=[],
    )

    pkg = AnswerPackage(
        package_id="pkg-1",
        query_id="q-1",
        raw_query="query",
        normalized_query="query",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="All grounded",
        reasoning_plan=plan,
        facts=[],
        calculations=[],
        reasoning_trace=[],
        claims=[],
        citations=[],
        evidence=[],
        grounding_validation=GroundingValidationResult(
            status=GroundingStatus.GROUNDED,
            total_claims=3,
            grounded_claims=3,
            ungrounded_claims=0,
            conflicting_claims=0,
            unverified_citations=0,
            validation_passed=True,
        ),
    )

    grd_metrics = evaluator.evaluate_grounding(pkg, case)
    assert grd_metrics.grounded_answer_rate == 1.0
    assert grd_metrics.unsupported_claim_rate == 0.0
    assert grd_metrics.grounding_failure_rate == 0.0
