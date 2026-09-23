"""Integration tests for Phase 12 LLM Output Validator Integrity and Fallback Handling."""

import pytest

from financial_rag.application.evaluation.runner import EvaluationRunner
from financial_rag.domain.entities.answer import (
    AnswerRequest,
    LLMAnswerOutput,
    ResponseStyle,
)
from financial_rag.domain.entities.evaluation import (
    EvaluationCase,
    EvaluationCategory,
    ExpectedCalculation,
    ExpectedFact,
)
from financial_rag.domain.entities.reasoning import (
    AnswerPackage,
    ReasoningOperation,
)
from financial_rag.infrastructure.llm.validator import DeterministicAnswerValidator


@pytest.fixture
def sample_answer_package() -> AnswerPackage:
    runner = EvaluationRunner()
    case = EvaluationCase(
        case_id="val-test-01",
        category=EvaluationCategory.NUMERICAL_REASONING,
        query="What was Apple's revenue in 2024 and its growth?",
        expected_document_ids=["doc-apple-2024"],
        expected_page_numbers=[45],
        expected_chunk_ids=["chunk-001"],
        expected_facts=[
            ExpectedFact(metric="Total Net Sales", expected_value="391035", scale="MILLIONS")
        ],
        expected_calculations=[
            ExpectedCalculation(
                operation=ReasoningOperation.PERCENTAGE_CHANGE,
                expected_result_str="2.0",
            )
        ],
        expected_citations_count=1,
    )
    pkg, _ = runner._build_standalone_case_package(case)
    return pkg


def test_validator_passes_valid_output(sample_answer_package):
    validator = DeterministicAnswerValidator()
    req = AnswerRequest(
        query=sample_answer_package.raw_query,
        response_style=ResponseStyle.STANDARD,
        include_citations=True,
    )
    llm_out = LLMAnswerOutput(
        summary="Apple reported total net sales of $391,035 million in FY2024 [C1].",
        detailed_answer="Apple's total net sales in fiscal 2024 were $391,035 million, representing a 2.0% increase [C1].",
        citation_markers=["[C1]"],
    )

    res = validator.validate_answer(
        llm_output=llm_out, answer_package=sample_answer_package, request=req
    )
    assert res.valid is True
    assert len(res.failures) == 0
    assert len(res.invalid_citations) == 0


def test_validator_catches_phantom_citation(sample_answer_package):
    validator = DeterministicAnswerValidator()
    req = AnswerRequest(query=sample_answer_package.raw_query)
    llm_out = LLMAnswerOutput(
        summary="Apple reported total net sales of $391,035 million [C1].",
        detailed_answer="Apple reported revenue of $391,035 million with growth [C99].",  # [C99] is phantom
        citation_markers=["[C1]", "[C99]"],
    )

    res = validator.validate_answer(
        llm_output=llm_out, answer_package=sample_answer_package, request=req
    )
    assert res.valid is False
    assert any(
        "phantom" in f.message.lower()
        or "invalid citation" in f.message.lower()
        or "marker" in f.message.lower()
        for f in res.failures
    )
    assert "[C99]" in res.invalid_citations


def test_validator_catches_empty_schema(sample_answer_package):
    validator = DeterministicAnswerValidator()
    req = AnswerRequest(query=sample_answer_package.raw_query)
    llm_out = LLMAnswerOutput(
        summary="",  # Empty summary
        detailed_answer="Detailed answer with some facts [C1].",
        citation_markers=["[C1]"],
    )

    res = validator.validate_answer(
        llm_output=llm_out, answer_package=sample_answer_package, request=req
    )
    assert res.valid is False
    assert any(f.stage == "schema" for f in res.failures)


def test_validator_catches_unverified_number(sample_answer_package):
    validator = DeterministicAnswerValidator()
    req = AnswerRequest(query=sample_answer_package.raw_query)
    llm_out = LLMAnswerOutput(
        summary="Here is the summary with ungrounded fact 888777666 [C1].",
        detailed_answer="Apple reported revenue of 888777666 million [C1].",
        citation_markers=["[C1]"],
    )

    res = validator.validate_answer(
        llm_output=llm_out, answer_package=sample_answer_package, request=req
    )
    assert res.valid is False
    assert len(res.numerical_discrepancies) > 0
    assert any(f.stage == "numerical_fidelity" for f in res.failures)
