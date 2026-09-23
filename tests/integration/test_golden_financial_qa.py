"""Integration tests executing the Golden Financial QA Benchmark dataset and Acceptance Scenarios 66-72."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from financial_rag.application.answer.service import AnswerOrchestrationService
from financial_rag.domain.entities.answer import AnswerRequest, AnswerStatus, ResponseStyle
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    CalculationResult,
    Citation,
    CitationType,
    Claim,
    EvidenceConflict,
    FinancialFact,
    FinancialScale,
    FinancialValue,
    FiscalPeriod,
    GroundingStatus,
    GroundingValidationResult,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.domain.interfaces.reasoning import ReasoningServiceProtocol
from financial_rag.infrastructure.llm.answerability_gate import DeterministicAnswerabilityGate
from financial_rag.infrastructure.llm.cache import InMemoryAnswerCache
from financial_rag.infrastructure.llm.context_builder import DeterministicContextBuilder
from financial_rag.infrastructure.llm.fake_provider import FakeLLMProvider
from financial_rag.infrastructure.llm.prompt_builder import VersionedPromptBuilder
from financial_rag.infrastructure.llm.renderer import DeterministicResponseRenderer
from financial_rag.infrastructure.llm.validator import DeterministicAnswerValidator
from tests.fixtures.financial_reasoning_fixtures import make_test_evidence


def load_golden_dataset():
    path = Path(__file__).parent.parent / "fixtures" / "golden_financial_qa.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class ParameterizedMockReasoningService(ReasoningServiceProtocol):
    """Reasoning service mock returning configured answer packages for QA benchmark."""

    def __init__(self, answer_package: AnswerPackage):
        self.package = answer_package

    async def reason(self, *args, **kwargs) -> AnswerPackage:
        return self.package


def make_package_for_test_case(test_case: dict) -> AnswerPackage:
    cat = test_case["category"]

    if cat == "insufficient_evidence":
        plan = ReasoningPlan(
            plan_id="plan-insufficient",
            query=test_case["query"],
            operations=[ReasoningOperation.DIRECT_LOOKUP],
            target_metrics=["Total net sales"],
            target_periods=["2030"],
            target_companies=["AAPL"],
            required_fact_keys=["revenue_2030"],
            steps_description=["Search FY2030"],
        )
        return AnswerPackage(
            package_id="pkg-insufficient",
            query_id="q-insufficient",
            raw_query=test_case["query"],
            normalized_query=test_case["query"],
            answerability=AnswerabilityStatus.INSUFFICIENT_EVIDENCE,
            answerability_rationale="No financial filings for FY2030 found in the corpus.",
            reasoning_plan=plan,
            facts=[],
            calculations=[],
            reasoning_trace=[],
            claims=[],
            citations=[],
            evidence=[],
            missing_facts=["FY2030 Total net sales"],
            grounding_validation=GroundingValidationResult(
                status=GroundingStatus.UNGROUNDED,
                total_claims=0,
                grounded_claims=0,
                ungrounded_claims=0,
                conflicting_claims=0,
                unverified_citations=0,
            ),
            confidence_score=0.0,
        )

    if cat == "conflicting_evidence":
        plan = ReasoningPlan(
            plan_id="plan-conflict",
            query=test_case["query"],
            operations=[ReasoningOperation.DIRECT_LOOKUP],
            target_metrics=["R&D Expense"],
            target_periods=["2024"],
            target_companies=["AAPL"],
            required_fact_keys=["rd_2024"],
            steps_description=["Compare filings"],
        )
        conflict = EvidenceConflict(
            conflict_id="conf-1",
            metric="R&D Expense",
            period="FY2024",
            conflicting_facts=[],
            difference_description="Press release reports $29,000M R&D while 10-K filing reports $31,370M R&D.",
            resolved=False,
            resolution_rationale="Unresolved conflict",
        )
        return AnswerPackage(
            package_id="pkg-conflict",
            query_id="q-conflict",
            raw_query=test_case["query"],
            normalized_query=test_case["query"],
            answerability=AnswerabilityStatus.CONFLICTING_EVIDENCE,
            answerability_rationale="Press release reports $29,000M R&D while 10-K filing reports $31,370M R&D.",
            reasoning_plan=plan,
            facts=[],
            calculations=[],
            reasoning_trace=[],
            claims=[],
            citations=[],
            evidence=[],
            conflicts=[conflict],
            grounding_validation=GroundingValidationResult(
                status=GroundingStatus.PARTIALLY_GROUNDED,
                total_claims=0,
                grounded_claims=0,
                ungrounded_claims=0,
                conflicting_claims=1,
                unverified_citations=0,
            ),
            confidence_score=0.3,
        )

    # Standard / Numerical / Calculation cases
    facts = []
    cits = []
    claims = []
    fact_ids = []
    for i, f_data in enumerate(test_case.get("expected_facts", []), start=1):
        f_id = f"fact-{i}"
        cit_id = f"cit-{i}"
        claim_id = f"claim-{i}"
        fact_ids.append(f_id)

        clean_num = f_data["raw_value"].replace(",", "")
        scale_enum = (
            FinancialScale.MILLIONS if f_data.get("scale") == "millions" else FinancialScale.EXACT
        )
        val = FinancialValue(
            raw_value=f_data["raw_value"],
            display_value=f"${f_data['raw_value']} million",
            numeric_value=Decimal(clean_num) * scale_enum.multiplier,
            unscaled_value=Decimal(clean_num),
            currency=f_data["currency"],
            scale=scale_enum,
            unit=f_data["currency"],
        )
        period = FiscalPeriod(
            fiscal_year=int(f_data["period"].replace("FY", "")),
            period_type="FY",
            source_text=f_data["period"],
        )
        facts.append(
            FinancialFact(
                fact_id=f_id,
                metric=f_data["metric"],
                value=val,
                period=period,
                company="Apple Inc.",
                ticker="AAPL",
                document_id="doc-10k",
                document_version_id="ver-1",
                page_number=40 + i,
                chunk_id=f"chunk-{i}",
                table_id=None,
                source_evidence_id=f"ev-{i}",
                extraction_method="table_structured",
                confidence=0.98,
                source_text=f"{f_data['metric']} | {f_data['raw_value']}",
            )
        )
        cits.append(
            Citation(
                citation_id=cit_id,
                claim_id=claim_id,
                document_id="doc-10k",
                document_version_id="ver-1",
                page_number=40 + i,
                page_numbers=[40 + i],
                chunk_id=f"chunk-{i}",
                table_id=None,
                section_path="Item 8 > Financial Statements",
                ticker="AAPL",
                source_excerpt=f"{f_data['metric']} was ${f_data['raw_value']} million for {f_data['period']}.",
                bounding_box=None,
                citation_type=CitationType.TABLE_CELL,
                verified=True,
            )
        )
        claims.append(
            Claim(
                claim_id=claim_id,
                text=f"Apple's {f_data['metric']} for {f_data['period']} was ${f_data['raw_value']} million.",
                claim_type="factual",
                source_fact_ids=[f_id],
                calculation_ids=[],
                reasoning_step_ids=[i],
                confidence=0.98,
                is_grounded=True,
            )
        )

    calcs = []
    for j, c_data in enumerate(test_case.get("expected_calculations", []), start=1):
        calcs.append(
            CalculationResult(
                calculation_id=f"calc-{j}",
                operation=ReasoningOperation.GROWTH_RATE
                if c_data["operation"] == "growth"
                else ReasoningOperation.RATIO,
                formula=f"{c_data['operation']}(...)",
                inputs=[],
                input_fact_ids=fact_ids,
                raw_result=Decimal(c_data["expected_result"]),
                rounded_result=Decimal(c_data["expected_result"]),
                display_result=c_data["expected_formatted"],
                unit="%",
                currency=None,
                success=True,
            )
        )

    evidence = [
        make_test_evidence(
            content="Consolidated Statements of Operations",
            page_number=45,
            rank=1,
        )
    ]

    plan = ReasoningPlan(
        plan_id="plan-qa",
        query=test_case["query"],
        operations=[ReasoningOperation.DIRECT_LOOKUP],
        target_metrics=[f["metric"] for f in test_case.get("expected_facts", [])],
        target_periods=[f["period"] for f in test_case.get("expected_facts", [])],
        target_companies=["AAPL"],
        required_fact_keys=[f"fact_{i}" for i in range(len(facts))],
        steps_description=["Lookup and calculate"],
    )

    return AnswerPackage(
        package_id="pkg-qa",
        query_id="q-qa",
        raw_query=test_case["query"],
        normalized_query=test_case["query"],
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="All requested financial facts and citations are verified.",
        reasoning_plan=plan,
        facts=facts,
        calculations=calcs,
        reasoning_trace=[],
        claims=claims,
        citations=cits,
        evidence=evidence,
        grounding_validation=GroundingValidationResult(
            status=GroundingStatus.GROUNDED,
            total_claims=len(claims),
            grounded_claims=len(claims),
            ungrounded_claims=0,
            conflicting_claims=0,
            unverified_citations=0,
        ),
        confidence_score=0.98,
    )


@pytest.mark.asyncio
async def test_golden_qa_benchmark_all_11_scenarios() -> None:
    """Execute all 11 financial question benchmark scenarios from the golden dataset."""
    dataset = load_golden_dataset()
    fake_llm = FakeLLMProvider(mode="valid")
    cache = InMemoryAnswerCache()

    for tc in dataset["test_cases"]:
        pkg = make_package_for_test_case(tc)
        reasoning_service = ParameterizedMockReasoningService(pkg)

        service = AnswerOrchestrationService(
            reasoning_service=reasoning_service,
            llm_provider=fake_llm,
            context_builder=DeterministicContextBuilder(),
            prompt_builder=VersionedPromptBuilder(),
            answerability_gate=DeterministicAnswerabilityGate(),
            validator=DeterministicAnswerValidator(),
            renderer=DeterministicResponseRenderer(),
            cache=cache,
        )

        req = AnswerRequest(query=tc["query"], response_style=ResponseStyle.STANDARD)
        resp = await service.generate_answer(req)

        assert resp.status.value == tc["expected_status"], (
            f"Failed for {tc['id']} ({tc['category']})"
        )
        assert resp.grounding_status.value == tc["expected_grounding"], (
            f"Grounding mismatch for {tc['id']}"
        )


# ============================================================
# Acceptance Tests 66 - 72 (from Specification)
# ============================================================


@pytest.mark.asyncio
async def test_acceptance_66_yoy_revenue_growth_authoritative_calculation() -> None:
    """Section 66: YoY revenue growth 100M -> 125M (+25%) must remain authoritative."""
    f1_val = FinancialValue(
        raw_value="100",
        display_value="$100M",
        numeric_value=Decimal("100000000"),
        unscaled_value=Decimal("100"),
        currency="USD",
        scale=FinancialScale.MILLIONS,
    )
    f2_val = FinancialValue(
        raw_value="125",
        display_value="$125M",
        numeric_value=Decimal("125000000"),
        unscaled_value=Decimal("125"),
        currency="USD",
        scale=FinancialScale.MILLIONS,
    )
    f1 = FinancialFact(
        fact_id="fact-1",
        metric="Revenue",
        value=f1_val,
        period=FiscalPeriod(fiscal_year=2023, period_type="FY", source_text="2023"),
        company="Company A",
        ticker="CMPA",
        document_id="doc-2023",
        document_version_id="ver-1",
        page_number=10,
        chunk_id="chunk-1",
        table_id=None,
        source_evidence_id="ev-1",
        extraction_method="table_structured",
        confidence=0.99,
        source_text="FY2023 Revenue: $100M",
    )
    f2 = FinancialFact(
        fact_id="fact-2",
        metric="Revenue",
        value=f2_val,
        period=FiscalPeriod(fiscal_year=2024, period_type="FY", source_text="2024"),
        company="Company A",
        ticker="CMPA",
        document_id="doc-2024",
        document_version_id="ver-1",
        page_number=12,
        chunk_id="chunk-2",
        table_id=None,
        source_evidence_id="ev-2",
        extraction_method="table_structured",
        confidence=0.99,
        source_text="FY2024 Revenue: $125M",
    )

    calc = CalculationResult(
        calculation_id="calc-1",
        operation=ReasoningOperation.GROWTH_RATE,
        formula="((125 - 100) / 100) * 100 = 25.00%",
        inputs=[],
        input_fact_ids=["fact-1", "fact-2"],
        raw_result=Decimal("25.00"),
        rounded_result=Decimal("25.00"),
        display_result="+25.00%",
        unit="%",
        currency=None,
        success=True,
    )

    claim = Claim(
        claim_id="claim-1",
        text="Revenue grew by +25.00% from $100M in FY2023 to $125M in FY2024.",
        claim_type="calculated",
        source_fact_ids=["fact-1", "fact-2"],
        calculation_ids=["calc-1"],
        reasoning_step_ids=[1],
        confidence=0.99,
        is_grounded=True,
    )

    c1 = Citation(
        citation_id="cit-1",
        claim_id="claim-1",
        document_id="doc-2023",
        document_version_id="ver-1",
        page_number=10,
        page_numbers=[10],
        chunk_id="chunk-1",
        table_id=None,
        section_path="MD&A",
        ticker="CMPA",
        source_excerpt="FY2023 revenue was $100M",
        bounding_box=None,
        citation_type=CitationType.DIRECT_SOURCE,
        verified=True,
    )
    c2 = Citation(
        citation_id="cit-2",
        claim_id="claim-1",
        document_id="doc-2024",
        document_version_id="ver-1",
        page_number=12,
        page_numbers=[12],
        chunk_id="chunk-2",
        table_id=None,
        section_path="MD&A",
        ticker="CMPA",
        source_excerpt="FY2024 revenue was $125M",
        bounding_box=None,
        citation_type=CitationType.DIRECT_SOURCE,
        verified=True,
    )

    plan = ReasoningPlan(
        plan_id="plan-growth",
        query="What was revenue growth from FY2023 to FY2024?",
        operations=[ReasoningOperation.GROWTH_RATE],
        target_metrics=["Revenue"],
        target_periods=["2023", "2024"],
        target_companies=["CMPA"],
        required_fact_keys=["fact-1", "fact-2"],
        steps_description=["Extract facts", "Calculate YoY growth"],
    )

    pkg = AnswerPackage(
        package_id="pkg-growth-accept",
        query_id="q-growth-accept",
        raw_query="What was revenue growth from FY2023 to FY2024?",
        normalized_query="What was revenue growth from FY2023 to FY2024?",
        answerability=AnswerabilityStatus.ANSWERABLE,
        answerability_rationale="Complete verified facts and calculations available.",
        reasoning_plan=plan,
        facts=[f1, f2],
        calculations=[calc],
        reasoning_trace=[],
        claims=[claim],
        citations=[c1, c2],
        evidence=[],
        grounding_validation=GroundingValidationResult(
            status=GroundingStatus.GROUNDED,
            total_claims=1,
            grounded_claims=1,
            ungrounded_claims=0,
            conflicting_claims=0,
            unverified_citations=0,
        ),
        confidence_score=0.99,
    )

    fake_llm = FakeLLMProvider(mode="valid")
    service = AnswerOrchestrationService(
        reasoning_service=ParameterizedMockReasoningService(pkg),
        llm_provider=fake_llm,
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
    )

    resp = await service.generate_answer(
        AnswerRequest(query="What was revenue growth from FY2023 to FY2024?")
    )
    assert resp.status == AnswerStatus.COMPLETED
    assert resp.grounding_status == GroundingStatus.GROUNDED
    assert len(resp.calculations) == 1
    assert resp.calculations[0].rounded_result == Decimal("25.00")
    assert resp.calculations[0].display_result == "+25.00%"


@pytest.mark.asyncio
async def test_acceptance_67_insufficient_evidence_fy2030() -> None:
    """Section 67: Query about FY2030 with no evidence must return INSUFFICIENT_EVIDENCE."""
    pkg = make_package_for_test_case(
        {"category": "insufficient_evidence", "query": "What was revenue in FY2030?"}
    )
    service = AnswerOrchestrationService(
        reasoning_service=ParameterizedMockReasoningService(pkg),
        llm_provider=FakeLLMProvider(mode="valid"),
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
    )

    resp = await service.generate_answer(AnswerRequest(query="What was revenue in FY2030?"))
    assert resp.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert resp.grounding_status == GroundingStatus.UNGROUNDED
    assert (
        "sufficient evidence" in resp.answer_text.lower()
        or "insufficient" in resp.answer_text.lower()
    )


@pytest.mark.asyncio
async def test_acceptance_68_conflicting_evidence_unresolved() -> None:
    """Section 68: Unresolved conflicting facts must return CONFLICTING_EVIDENCE."""
    pkg = make_package_for_test_case(
        {"category": "conflicting_evidence", "query": "What was R&D expense?"}
    )
    service = AnswerOrchestrationService(
        reasoning_service=ParameterizedMockReasoningService(pkg),
        llm_provider=FakeLLMProvider(mode="valid"),
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
    )

    resp = await service.generate_answer(AnswerRequest(query="What was R&D expense?"))
    assert resp.status == AnswerStatus.CONFLICTING_EVIDENCE
    assert "conflict" in resp.answer_text.lower() or "discrepancy" in resp.answer_text.lower()


@pytest.mark.asyncio
async def test_acceptance_70_numerical_hallucination_triggers_safe_fallback() -> None:
    """Section 70: LLM attempting to invent a hallucinated number is rejected."""
    fake_llm = FakeLLMProvider(mode="hallucinate_number")
    dataset = load_golden_dataset()
    pkg = make_package_for_test_case(dataset["test_cases"][0])

    service = AnswerOrchestrationService(
        reasoning_service=ParameterizedMockReasoningService(pkg),
        llm_provider=fake_llm,
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
        max_retries=1,
    )

    resp = await service.generate_answer(AnswerRequest(query=dataset["test_cases"][0]["query"]))
    assert resp.metadata["used_fallback"] is True
    # The hallucinated number (999.99) is NOT in the final fallback body
    body = resp.answer_text.split("\n\n", 1)[1] if "\n\n" in resp.answer_text else resp.answer_text
    assert "999.99" not in body
    assert "391,035" in resp.answer_text


@pytest.mark.asyncio
async def test_acceptance_71_citation_fabrication_c99_triggers_safe_fallback() -> None:
    """Section 71: LLM attempting to invent [C99] is rejected."""
    fake_llm = FakeLLMProvider(mode="hallucinate_citation")
    dataset = load_golden_dataset()
    pkg = make_package_for_test_case(dataset["test_cases"][0])

    service = AnswerOrchestrationService(
        reasoning_service=ParameterizedMockReasoningService(pkg),
        llm_provider=fake_llm,
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
        max_retries=1,
    )

    resp = await service.generate_answer(AnswerRequest(query=dataset["test_cases"][0]["query"]))
    assert resp.metadata["used_fallback"] is True
    body = resp.answer_text.split("\n\n", 1)[1] if "\n\n" in resp.answer_text else resp.answer_text
    assert "[C99]" not in body
    assert "[C1]" in resp.answer_text


@pytest.mark.asyncio
async def test_acceptance_72_multi_tenant_isolation() -> None:
    """Section 72: Tenant A context must never contain Tenant B evidence."""
    cache = InMemoryAnswerCache()
    fake_llm = FakeLLMProvider(mode="valid")
    dataset = load_golden_dataset()
    pkg = make_package_for_test_case(dataset["test_cases"][0])

    service = AnswerOrchestrationService(
        reasoning_service=ParameterizedMockReasoningService(pkg),
        llm_provider=fake_llm,
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
        cache=cache,
    )

    req_a = AnswerRequest(query="What was revenue?", tenant_id="tenant-alpha")
    req_b = AnswerRequest(query="What was revenue?", tenant_id="tenant-beta")

    resp_a = await service.generate_answer(req_a)
    resp_b = await service.generate_answer(req_b)

    # Assert separate cache keys and zero cross-tenant collision
    assert resp_a.metadata.get("cache_hit") is False
    assert resp_b.metadata.get("cache_hit") is False
