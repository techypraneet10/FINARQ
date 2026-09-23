"""OpenAI / Generic REST Large Language Model provider adapter."""

import json
from collections.abc import AsyncIterator
from typing import Any, NoReturn, TypeVar, cast

from financial_rag.config.settings import LLMSettings, get_settings
from financial_rag.domain.exceptions import (
    LLMOutputFormatError,
    LLMProviderError,
    LLMTimeoutError,
)
from financial_rag.domain.interfaces.llm import LLMProviderProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.llm.openai")

T = TypeVar("T")


class OpenAILLMProvider(LLMProviderProtocol):
    """Generates structured and unstructured text completions using OpenAI API."""

    def __init__(self, llm_settings: LLMSettings | None = None) -> None:
        self._settings = llm_settings or get_settings().llm
        self._model_name = self._settings.model_name
        self._client: Any = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import AsyncOpenAI

                api_key = self._settings.api_key.get_secret_value()
                self._client = AsyncOpenAI(
                    api_key=api_key if api_key else "dummy-api-key",
                    timeout=float(self._settings.request_timeout_seconds),
                    max_retries=self._settings.max_retries,
                )
            except ImportError as ex:
                raise LLMProviderError(
                    provider="openai",
                    message="The 'openai' package is required to use OpenAILLMProvider.",
                ) from ex
        return self._client

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate unstructured text completion."""
        try:
            client = self._get_client()
            messages: list[dict[str, str]] = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop_sequences,
            )
            content = response.choices[0].message.content or ""
            return content
        except Exception as ex:
            self._handle_exception(ex)

    async def structured_generate(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output adhering to a validated schema."""
        try:
            client = self._get_client()
            messages: list[dict[str, str]] = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = await client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content or "{}"
            parsed_json = json.loads(raw_text)

            if hasattr(response_schema, "__dataclass_fields__"):
                return response_schema(**parsed_json)
            if hasattr(response_schema, "model_validate"):
                return cast("T", response_schema.model_validate(parsed_json))  # type: ignore[attr-defined]
            return response_schema(**parsed_json)
        except json.JSONDecodeError as ex:
            raise LLMOutputFormatError(
                raw_output=raw_text if "raw_text" in locals() else "",
                expected_schema=str(response_schema),
                message=f"Failed to parse LLM response as JSON: {ex}",
            ) from ex
        except Exception as ex:
            self._handle_exception(ex)

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream token chunks asynchronously from OpenAI API."""
        try:
            client = self._get_client()
            messages: list[dict[str, str]] = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            stream = await client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as ex:
            self._handle_exception(ex)

    async def health_check(self) -> bool:
        """Verify OpenAI API connectivity."""
        try:
            client = self._get_client()
            # Minimal health check
            resp = await client.chat.completions.create(
                model=self._model_name,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return bool(resp.choices)
        except Exception:
            return False

    def _handle_exception(self, ex: Exception) -> NoReturn:
        ex_str = str(ex).lower()
        if "timeout" in ex_str or "timed out" in ex_str:
            raise LLMTimeoutError(
                provider="openai",
                timeout_seconds=float(self._settings.request_timeout_seconds),
            ) from ex
        raise LLMProviderError(
            provider="openai",
            message=f"OpenAI LLM execution failed: {ex}",
            details={"model": self._model_name, "error": str(ex)},
        ) from ex
