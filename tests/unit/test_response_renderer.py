"""Unit tests for DeterministicResponseRenderer."""

from financial_rag.domain.entities.answer import (
    AnswerRequest,
    LLMAnswerOutput,
    ResponseStyle,
    ValidationResult,
)
from financial_rag.infrastructure.llm.renderer import DeterministicResponseRenderer
from tests.unit.test_context_builder import make_test_answer_package


def test_renderer_concise_style() -> None:
    renderer = DeterministicResponseRenderer()
    pkg = make_test_answer_package()
    req = AnswerRequest(query="What was growth?", response_style=ResponseStyle.CONCISE)
    output = LLMAnswerOutput(
        summary="Apple revenue grew 2.02% to $391,035 million in FY2024 [C1].",
        detailed_answer="Apple Inc. revenue grew 2.02% in FY2024.",
        calculation_explanation="Growth = +2.02%",
    )
    val = ValidationResult(valid=True)

    text = renderer.render_response(output, pkg, req, val)
    assert "Apple revenue grew 2.02%" in text
    assert "**[C1]**: Document `doc-10k-2024`" in text


def test_renderer_analytical_style() -> None:
    renderer = DeterministicResponseRenderer()
    pkg = make_test_answer_package()
    req = AnswerRequest(query="Analyze revenue", response_style=ResponseStyle.ANALYTICAL)
    output = LLMAnswerOutput(
        summary="Apple net sales overview.",
        detailed_answer="Apple demonstrated consistent top-line growth of +2.02% [C1].",
        calculation_explanation="Formula: ((391035 - 383285) / 383285) * 100",
        limitations_disclosed=["Product-level breakdown not provided."],
    )
    val = ValidationResult(valid=True)

    text = renderer.render_response(output, pkg, req, val)
    assert "### Analysis" in text
    assert "Deterministic Formula" in text
    assert "Product-level breakdown not provided" in text


def test_renderer_deterministic_fallback() -> None:
    renderer = DeterministicResponseRenderer()
    pkg = make_test_answer_package()
    req = AnswerRequest(query="What was growth?")

    text = renderer.render_deterministic_fallback(pkg, req, "Provider timeout")
    assert "Fallback Answer - Provider timeout" in text
    assert "Total net sales increased by +2.02%" in text
    assert "Verified Calculation:" in text
    assert "Sources & Citations" in text
