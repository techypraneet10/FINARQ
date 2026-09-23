"""Integration tests verifying strict prevention of LLM hallucinations and enforcement of numerical/citation fidelity."""

import pytest

from financial_rag.application.answer.service import AnswerOrchestrationService
from financial_rag.domain.entities.answer import AnswerRequest
from financial_rag.domain.interfaces.reasoning import ReasoningServiceProtocol
from financial_rag.infrastructure.llm.answerability_gate import DeterministicAnswerabilityGate
from financial_rag.infrastructure.llm.context_builder import DeterministicContextBuilder
from financial_rag.infrastructure.llm.fake_provider import FakeLLMProvider
from financial_rag.infrastructure.llm.prompt_builder import VersionedPromptBuilder
from financial_rag.infrastructure.llm.renderer import DeterministicResponseRenderer
from financial_rag.infrastructure.llm.validator import DeterministicAnswerValidator
from tests.unit.test_context_builder import make_test_answer_package


class MockReasoningService(ReasoningServiceProtocol):
    async def reason(self, *args, **kwargs):
        return make_test_answer_package()


@pytest.mark.asyncio
async def test_hallucinated_number_triggers_safe_fallback() -> None:
    # LLM configured to hallucinate $999.99 billion
    fake_llm = FakeLLMProvider(mode="hallucinate_number")
    answer_service = AnswerOrchestrationService(
        reasoning_service=MockReasoningService(),
        llm_provider=fake_llm,
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
        max_retries=1,
    )

    req = AnswerRequest(query="What was Apple's revenue?")
    response = await answer_service.generate_answer(req)

    # Assert that the hallucinated number $999.99 billion was NOT in fallback body!
    assert response.metadata["used_fallback"] is True
    assert "Fallback Answer" in response.answer_text
    body = (
        response.answer_text.split("\n\n", 1)[1]
        if "\n\n" in response.answer_text
        else response.answer_text
    )
    assert "999.99" not in body
    assert "Total net sales" in response.answer_text
    assert "+2.02%" in response.answer_text


@pytest.mark.asyncio
async def test_hallucinated_citation_triggers_safe_fallback() -> None:
    # LLM configured to hallucinate [C99]
    fake_llm = FakeLLMProvider(mode="hallucinate_citation")
    answer_service = AnswerOrchestrationService(
        reasoning_service=MockReasoningService(),
        llm_provider=fake_llm,
        context_builder=DeterministicContextBuilder(),
        prompt_builder=VersionedPromptBuilder(),
        answerability_gate=DeterministicAnswerabilityGate(),
        validator=DeterministicAnswerValidator(),
        renderer=DeterministicResponseRenderer(),
        max_retries=1,
    )

    req = AnswerRequest(query="What was Apple's revenue?")
    response = await answer_service.generate_answer(req)

    # Assert that [C99] is NOT cited in fallback answer body!
    assert response.metadata["used_fallback"] is True
    body = (
        response.answer_text.split("\n\n", 1)[1]
        if "\n\n" in response.answer_text
        else response.answer_text
    )
    assert "[C99]" not in body
    assert "[C1]" in response.answer_text
