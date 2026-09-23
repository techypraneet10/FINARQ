"""Unit tests for VersionedPromptBuilder."""

from financial_rag.domain.entities.answer import AnswerRequest, ResponseStyle
from financial_rag.infrastructure.llm.prompt_builder import PROMPT_VERSION, VersionedPromptBuilder
from tests.unit.test_context_builder import make_test_answer_package


def test_prompt_builder_versioning_and_instructions() -> None:
    builder = VersionedPromptBuilder()
    pkg = make_test_answer_package()
    req = AnswerRequest(
        query="What was Apple's revenue growth in 2024?",
        response_style=ResponseStyle.STANDARD,
    )
    prompt, system_inst, version = builder.build_prompt(req, "<CONTEXT>...</CONTEXT>", pkg)

    assert version == PROMPT_VERSION
    assert "UNTRUSTED DATA BOUNDARY" in system_inst
    assert "DO NOT CALCULATE" in system_inst
    assert "TARGET RESPONSE STYLE: STANDARD" in prompt
    assert "=== VERIFIED CONTEXT START ===" in prompt


def test_prompt_builder_different_styles() -> None:
    builder = VersionedPromptBuilder()
    pkg = make_test_answer_package()

    # Concise style
    req_concise = AnswerRequest(
        query="What was Apple's revenue growth in 2024?",
        response_style=ResponseStyle.CONCISE,
    )
    prompt_c, _, _ = builder.build_prompt(req_concise, "context", pkg)
    assert "TARGET RESPONSE STYLE: CONCISE" in prompt_c
    assert "1-2 sentence" in prompt_c

    # Analytical style
    req_ana = AnswerRequest(
        query="What was Apple's revenue growth in 2024?",
        response_style=ResponseStyle.ANALYTICAL,
    )
    prompt_a, _, _ = builder.build_prompt(req_ana, "context", pkg)
    assert "TARGET RESPONSE STYLE: ANALYTICAL" in prompt_a
    assert "analytical commentary" in prompt_a
