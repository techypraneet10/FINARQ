"""Unit tests for OpenAILLMProvider."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, SecretStr

from financial_rag.config.settings import LLMSettings
from financial_rag.domain.exceptions import LLMOutputFormatError, LLMProviderError, LLMTimeoutError
from financial_rag.infrastructure.llm.openai_provider import OpenAILLMProvider


class SampleSchema(BaseModel):
    summary: str
    amount: float


@pytest.fixture
def openai_settings():
    return LLMSettings(
        provider="openai",
        model_name="gpt-4o",
        api_key=SecretStr("test-openai-key-12345"),
        request_timeout_seconds=5,
    )


@pytest.mark.asyncio
async def test_openai_llm_provider_generate(openai_settings):
    provider = OpenAILLMProvider(llm_settings=openai_settings)

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Sample unstructured completion."
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    provider._client = mock_client

    result = await provider.generate(
        prompt="What was 2024 revenue?", system_instruction="Be helpful."
    )
    assert result == "Sample unstructured completion."
    mock_client.chat.completions.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_openai_llm_provider_structured_generate(openai_settings):
    provider = OpenAILLMProvider(llm_settings=openai_settings)

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"summary": "Total net sales was $391B", "amount": 391035.0}'
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    provider._client = mock_client

    result = await provider.structured_generate(
        prompt="Analyze revenue", response_schema=SampleSchema
    )
    assert isinstance(result, SampleSchema)
    assert result.summary == "Total net sales was $391B"
    assert result.amount == 391035.0


@pytest.mark.asyncio
async def test_openai_llm_provider_structured_generate_malformed_json(openai_settings):
    provider = OpenAILLMProvider(llm_settings=openai_settings)

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Not valid JSON {"
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_resp)

    provider._client = mock_client

    with pytest.raises(LLMOutputFormatError):
        await provider.structured_generate(prompt="Analyze revenue", response_schema=SampleSchema)


@pytest.mark.asyncio
async def test_openai_llm_provider_streaming(openai_settings):
    provider = OpenAILLMProvider(llm_settings=openai_settings)

    class MockStream:
        def __init__(self, token_list):
            self.tokens = token_list

        async def __aiter__(self):
            for t in self.tokens:
                chunk = MagicMock()
                choice = MagicMock()
                choice.delta.content = t
                chunk.choices = [choice]
                yield chunk

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MockStream(["Apple ", "total ", "sales ", "grew."])
    )
    provider._client = mock_client

    chunks = []
    async for chunk in provider.generate_stream(prompt="Stream test"):
        chunks.append(chunk)

    assert chunks == ["Apple ", "total ", "sales ", "grew."]


@pytest.mark.asyncio
async def test_openai_llm_provider_timeout_exception(openai_settings):
    provider = OpenAILLMProvider(llm_settings=openai_settings)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=TimeoutError("Request timed out"))
    provider._client = mock_client

    with pytest.raises(LLMTimeoutError):
        await provider.generate(prompt="Timeout test")


@pytest.mark.asyncio
async def test_openai_llm_provider_general_error_exception(openai_settings):
    provider = OpenAILLMProvider(llm_settings=openai_settings)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=RuntimeError("503 Service Unavailable")
    )
    provider._client = mock_client

    with pytest.raises(LLMProviderError):
        await provider.generate(prompt="Error test")
