"""Architectural contract for provider-agnostic Large Language Models."""

from collections.abc import AsyncIterator
from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Contract for LLM generation and structured extraction."""

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> str:
        """Generate unstructured text completion."""
        ...

    async def structured_generate(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        """Generate structured output adhering to a validated schema."""
        ...

    def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream token chunks asynchronously from the LLM provider."""
        ...

    async def health_check(self) -> bool:
        """Verify LLM service provider connectivity."""
        ...
