"""Unit tests for DeterministicAnswerValidator."""

from financial_rag.domain.entities.answer import AnswerRequest, LLMAnswerOutput, LLMAnswerSection
from financial_rag.infrastructure.llm.validator import DeterministicAnswerValidator
from tests.unit.test_context_builder import make_test_answer_package


def test_validator_passes_valid_output() -> None:
    validator = DeterministicAnswerValidator()
    pkg = make_test_answer_package()
    req = AnswerRequest(query="What was revenue?")
    valid_output = LLMAnswerOutput(
        summary="Apple reported total net sales of $391,035 million in FY2024 [C1].",
        detailed_answer="Apple Inc. net sales were $391,035 million for FY2024, increasing by 2.02% [C1].",
        sections=[
            LLMAnswerSection(
                heading="Summary",
                content="Total net sales were $391,035 million [C1].",
                claim_ids=["claim-1"],
                citation_markers=["[C1]"],
            )
        ],
        calculation_explanation="Growth = +2.02%",
        cited_claim_ids=["claim-1"],
        citation_markers=["[C1]"],
    )

    res = validator.validate_answer(valid_output, pkg, req)
    assert res.valid is True
    assert len(res.failures) == 0


def test_validator_rejects_unknown_citation_marker() -> None:
    validator = DeterministicAnswerValidator()
    pkg = make_test_answer_package()  # only has [C1]
    req = AnswerRequest(query="What was revenue?")
    invalid_citation_output = LLMAnswerOutput(
        summary="Revenue was $391,035 million [C99].",  # [C99] is unknown!
        detailed_answer="Revenue was $391,035 million [C99].",
        sections=[],
        cited_claim_ids=["claim-1"],
        citation_markers=["[C99]"],
    )

    res = validator.validate_answer(invalid_citation_output, pkg, req)
    assert res.valid is False
    assert "[C99]" in res.invalid_citations
    assert any(f.code == "UNKNOWN_CITATION_MARKER" for f in res.failures)


def test_validator_rejects_hallucinated_number() -> None:
    validator = DeterministicAnswerValidator()
    pkg = make_test_answer_package()  # has 391035, 2.02, 2024
    req = AnswerRequest(query="What was revenue?")
    hallucinated_number_output = LLMAnswerOutput(
        summary="Revenue surged to $999,999 million in FY2024 [C1].",  # 999999 is unverified!
        detailed_answer="Revenue surged to $999,999 million in FY2024 [C1].",
        sections=[],
        cited_claim_ids=["claim-1"],
        citation_markers=["[C1]"],
    )

    res = validator.validate_answer(hallucinated_number_output, pkg, req)
    assert res.valid is False
    assert any(f.code == "UNVERIFIED_NUMBER" for f in res.failures)


def test_validator_rejects_empty_summary() -> None:
    validator = DeterministicAnswerValidator()
    pkg = make_test_answer_package()
    req = AnswerRequest(query="What was revenue?")
    empty_output = LLMAnswerOutput(
        summary="",
        detailed_answer="Some content [C1]",
        sections=[],
    )

    res = validator.validate_answer(empty_output, pkg, req)
    assert res.valid is False
    assert any(f.code == "EMPTY_SUMMARY" for f in res.failures)
