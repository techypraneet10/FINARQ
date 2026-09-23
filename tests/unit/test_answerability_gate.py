"""Unit tests for DeterministicAnswerabilityGate."""

from dataclasses import replace

from financial_rag.domain.entities.answer import AnswerRequest, AnswerStatus
from financial_rag.domain.entities.reasoning import AnswerabilityStatus, EvidenceConflict
from financial_rag.infrastructure.llm.answerability_gate import DeterministicAnswerabilityGate
from tests.unit.test_context_builder import make_test_answer_package


def test_gate_allows_answerable_query() -> None:
    gate = DeterministicAnswerabilityGate()
    pkg = make_test_answer_package()
    req = AnswerRequest(query="What was revenue?")

    res = gate.evaluate_gate(pkg, req)
    assert res is None  # Allowed to proceed to LLM synthesis


def test_gate_intercepts_insufficient_evidence() -> None:
    gate = DeterministicAnswerabilityGate()
    pkg = make_test_answer_package()
    pkg = replace(
        pkg,
        answerability=AnswerabilityStatus.INSUFFICIENT_EVIDENCE,
        missing_facts=["revenue_2030"],
    )
    req = AnswerRequest(query="What will revenue be in 2030?")

    res = gate.evaluate_gate(pkg, req)
    assert res is not None
    assert res.status == AnswerStatus.INSUFFICIENT_EVIDENCE
    assert "sufficient evidence" in res.answer_text.lower()
    assert "revenue_2030" in res.answer_text


def test_gate_intercepts_conflicting_evidence() -> None:
    gate = DeterministicAnswerabilityGate()
    pkg = make_test_answer_package()
    pkg = replace(
        pkg,
        answerability=AnswerabilityStatus.CONFLICTING_EVIDENCE,
        conflicts=[
            EvidenceConflict(
                conflict_id="c-1",
                metric="Revenue",
                period="FY2024",
                conflicting_facts=pkg.facts,
                difference_description="Table reports $391B vs Narrative reports $390B",
                resolved=False,
            )
        ],
    )
    req = AnswerRequest(query="What was revenue?")

    res = gate.evaluate_gate(pkg, req)
    assert res is not None
    assert res.status == AnswerStatus.CONFLICTING_EVIDENCE
    assert "conflicting evidence" in res.answer_text.lower()
    assert "Table reports $391B" in res.answer_text


def test_gate_intercepts_calculation_failed() -> None:
    gate = DeterministicAnswerabilityGate()
    pkg = make_test_answer_package()
    failed_calc = replace(
        pkg.calculations[0],
        success=False,
        error_message="Division by zero",
    )
    pkg = replace(
        pkg,
        answerability=AnswerabilityStatus.CALCULATION_FAILED,
        calculations=[failed_calc],
    )
    req = AnswerRequest(query="What was margin?")

    res = gate.evaluate_gate(pkg, req)
    assert res is not None
    assert res.status == AnswerStatus.CALCULATION_FAILED
    assert "Division by zero" in res.answer_text
