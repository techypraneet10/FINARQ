"""Architectural protocol contracts for Phase 4 LLM Answer Orchestration."""

from collections.abc import AsyncIterator
from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.answer import (
    AnswerRequest,
    AnswerResponse,
    AnswerStreamEvent,
    LLMAnswerOutput,
    ValidationResult,
)
from financial_rag.domain.entities.reasoning import AnswerPackage


@runtime_checkable
class ContextBuilderProtocol(Protocol):
    """Contract for packaging AnswerPackage into budgeted, structured context blocks."""

    def build_context(
        self,
        answer_package: AnswerPackage,
        max_tokens: int = 4000,
    ) -> str:
        """Construct cleanly delimited context block from verified AnswerPackage."""
        ...


@runtime_checkable
class PromptBuilderProtocol(Protocol):
    """Contract for constructing versioned, instruction-defended prompt templates."""

    def build_prompt(
        self,
        request: AnswerRequest,
        context: str,
        answer_package: AnswerPackage,
    ) -> tuple[str, str, str]:
        """Construct user prompt, system instructions, and return prompt version identifier."""
        ...

    def build_correction_prompt(
        self,
        base_prompt: str,
        failures: list[Any],
    ) -> str:
        """Construct a refined prompt incorporating validation failure feedback."""
        ...


@runtime_checkable
class AnswerabilityGateProtocol(Protocol):
    """Contract for inspecting AnswerPackage and generating deterministic responses for non-answerable states."""

    def evaluate_gate(
        self,
        answer_package: AnswerPackage,
        request: AnswerRequest,
    ) -> AnswerResponse | None:
        """Return deterministic AnswerResponse if question is non-answerable, or None to proceed to LLM."""
        ...


@runtime_checkable
class AnswerValidatorProtocol(Protocol):
    """Contract for 8-stage post-generation validation of LLM synthesis output."""

    def validate_answer(
        self,
        llm_output: LLMAnswerOutput,
        answer_package: AnswerPackage,
        request: AnswerRequest,
    ) -> ValidationResult:
        """Audit LLM output for schema, citation markers, claims, numerical fidelity, and grounding."""
        ...


@runtime_checkable
class ResponseRendererProtocol(Protocol):
    """Contract for rendering validated structured output into the final presentation format."""

    def render_response(
        self,
        llm_output: LLMAnswerOutput,
        answer_package: AnswerPackage,
        request: AnswerRequest,
        validation_result: ValidationResult,
    ) -> str:
        """Render final human-readable answer string with preserved citations and calculations."""
        ...

    def render_deterministic_fallback(
        self,
        answer_package: AnswerPackage,
        request: AnswerRequest,
        reason: str,
    ) -> str:
        """Render safe deterministic fallback answer directly from AnswerPackage."""
        ...


@runtime_checkable
class AnswerCacheProtocol(Protocol):
    """Contract for auditable answer caching."""

    async def get(self, cache_key: str) -> AnswerResponse | None:
        """Retrieve cached AnswerResponse."""
        ...

    async def set(
        self,
        cache_key: str,
        response: AnswerResponse,
        ttl_seconds: int = 3600,
    ) -> None:
        """Store AnswerResponse in cache."""
        ...

    def build_cache_key(
        self,
        request: AnswerRequest,
        package_id: str,
        prompt_version: str,
        model_name: str,
    ) -> str:
        """Generate deterministic cache key."""
        ...


@runtime_checkable
class AnswerOrchestratorServiceProtocol(Protocol):
    """Master contract for end-to-end Answer Orchestration Service."""

    async def generate_answer(
        self,
        request: AnswerRequest,
    ) -> AnswerResponse:
        """Execute end-to-end retrieval, reasoning, gated LLM synthesis, validation, and rendering."""
        ...

    def generate_answer_stream(
        self,
        request: AnswerRequest,
    ) -> AsyncIterator[AnswerStreamEvent]:
        """Stream progressive verified answer synthesis events."""
        ...
