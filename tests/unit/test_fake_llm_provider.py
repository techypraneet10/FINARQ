"""Unit tests for FakeLLMProvider."""

import pytest

from financial_rag.domain.entities.answer import LLMAnswerOutput
from financial_rag.domain.exceptions import LLMOutputFormatError, LLMProviderError, LLMTimeoutError
from financial_rag.infrastructure.llm.fake_provider import FakeLLMProvider


@pytest.mark.asyncio
async def test_fake_llm_valid_generation() -> None:
    provider = FakeLLMProvider(mode="valid")
    res = await provider.structured_generate("Test prompt", LLMAnswerOutput)
    assert res.summary is not None
    assert "Apple" in res.summary
    assert res.citation_markers == ["[C1]"]
    assert provider.call_count == 1
    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_fake_llm_hallucinate_citation_mode() -> None:
    provider = FakeLLMProvider(mode="hallucinate_citation")
    res = await provider.structured_generate("Test prompt", LLMAnswerOutput)
    assert "[C99]" in res.citation_markers


@pytest.mark.asyncio
async def test_fake_llm_hallucinate_number_mode() -> None:
    provider = FakeLLMProvider(mode="hallucinate_number")
    res = await provider.structured_generate("Test prompt", LLMAnswerOutput)
    assert "999.99" in res.summary


@pytest.mark.asyncio
async def test_fake_llm_timeout_mode() -> None:
    provider = FakeLLMProvider(mode="timeout")
    with pytest.raises(LLMTimeoutError):
        await provider.structured_generate("Test prompt", LLMAnswerOutput)


@pytest.mark.asyncio
async def test_fake_llm_error_mode() -> None:
    provider = FakeLLMProvider(mode="error")
    assert await provider.health_check() is False
    with pytest.raises(LLMProviderError):
        await provider.structured_generate("Test prompt", LLMAnswerOutput)


@pytest.mark.asyncio
async def test_fake_llm_malformed_json_mode() -> None:
    provider = FakeLLMProvider(mode="malformed_json")
    with pytest.raises(LLMOutputFormatError):
        await provider.structured_generate("Test prompt", LLMAnswerOutput)


@pytest.mark.asyncio
async def test_fake_llm_streaming_generation() -> None:
    provider = FakeLLMProvider(mode="valid")
    chunks = []
    async for chunk in provider.generate_stream("Test prompt"):
        chunks.append(chunk)

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "Apple" in full_text
