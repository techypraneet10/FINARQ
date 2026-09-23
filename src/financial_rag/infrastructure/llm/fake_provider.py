"""Deterministic Fake LLM Provider for testing, safety validation, and CI."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any, TypeVar

from financial_rag.domain.entities.answer import LLMAnswerOutput, LLMAnswerSection
from financial_rag.domain.exceptions import LLMOutputFormatError, LLMProviderError, LLMTimeoutError
from financial_rag.domain.interfaces.llm import LLMProviderProtocol

T = TypeVar("T")


class FakeLLMProvider(LLMProviderProtocol):
    """Deterministic, configurable LLM provider simulator."""

    def __init__(
        self,
        mode: str = "valid",  # "valid", "hallucinate_number", "hallucinate_citation", "unsupported_claim", "malformed_json", "timeout", "error"
        delay_seconds: float = 0.0,
        model_name: str = "fake-financial-llm-v1",
    ) -> None:
        self.mode = mode
        self.delay_seconds = delay_seconds
        self.model_name = model_name
        self.call_count = 0
        self.last_prompt: str | None = None
        self.last_system_instruction: str | None = None

    async def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        stop_sequences: list[str] | None = None,
    ) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.mode == "timeout":
            raise LLMTimeoutError(
                provider="fake_llm",
                timeout_seconds=self.delay_seconds or 0.1,
            )

        if self.mode == "error":
            raise LLMProviderError(
                provider="fake_llm",
                message="Simulated upstream provider outage (503 Service Unavailable).",
            )

        if self.mode == "malformed_json":
            return "This is not JSON: {invalid"

        return json.dumps(self._build_fake_payload())

    async def generate_stream(
        self,
        prompt: str,
        system_instruction: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction

        if self.mode == "timeout":
            raise LLMTimeoutError(
                provider="fake_llm",
                timeout_seconds=self.delay_seconds or 0.1,
            )

        if self.mode == "error":
            raise LLMProviderError(
                provider="fake_llm",
                message="Simulated upstream provider outage (503 Service Unavailable).",
            )

        full_text = self._build_fake_payload()["detailed_answer"]
        tokens = full_text.split(" ")
        for i, token in enumerate(tokens):
            if self.delay_seconds > 0:
                await asyncio.sleep(self.delay_seconds / max(len(tokens), 1))
            suffix = " " if i < len(tokens) - 1 else ""
            yield token + suffix

    async def structured_generate(
        self,
        prompt: str,
        response_schema: type[T],
        system_instruction: str | None = None,
        temperature: float = 0.0,
    ) -> T:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_instruction = system_instruction

        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        if self.mode == "timeout":
            raise LLMTimeoutError(
                provider="fake_llm",
                timeout_seconds=self.delay_seconds or 0.1,
            )

        if self.mode == "error":
            raise LLMProviderError(
                provider="fake_llm",
                message="Simulated upstream provider outage.",
            )

        if self.mode == "malformed_json":
            raise LLMOutputFormatError(
                raw_output="INVALID_PAYLOAD",
                expected_schema=str(response_schema),
            )

        payload = self._build_fake_payload()

        if response_schema is LLMAnswerOutput:
            return LLMAnswerOutput(
                summary=payload["summary"],
                detailed_answer=payload["detailed_answer"],
                sections=[LLMAnswerSection(**s) for s in payload.get("sections", [])],
                calculation_explanation=payload.get("calculation_explanation"),
                cited_claim_ids=payload.get("cited_claim_ids", []),
                citation_markers=payload.get("citation_markers", []),
                limitations_disclosed=payload.get("limitations_disclosed", []),
                warnings=payload.get("warnings", []),
            )  # type: ignore[return-value]

        # Generic schema mapping
        try:
            instance: T = response_schema(**payload)
            return instance
        except Exception as e:
            raise LLMOutputFormatError(
                raw_output=json.dumps(payload),
                expected_schema=str(response_schema),
                message=f"Could not instantiate schema: {e}",
            ) from e

    async def health_check(self) -> bool:
        return self.mode != "error"

    def _build_fake_payload(self) -> dict[str, Any]:
        """Construct synthetic payload based on configured mode."""
        if self.mode == "hallucinate_number":
            return {
                "summary": "Revenue in 2024 was $999.99 billion.",  # Hallucinated number
                "detailed_answer": "According to the financial statements, revenue surged to $999.99 billion [C1].",
                "sections": [
                    {
                        "heading": "Overview",
                        "content": "Revenue was $999.99 billion.",
                        "claim_ids": ["claim-1"],
                        "citation_markers": ["[C1]"],
                    }
                ],
                "calculation_explanation": None,
                "cited_claim_ids": ["claim-1"],
                "citation_markers": ["[C1]"],
                "limitations_disclosed": [],
                "warnings": [],
            }

        if self.mode == "hallucinate_citation":
            return {
                "summary": "Revenue was $391.035 billion in 2024 [C99].",  # Unknown citation [C99]
                "detailed_answer": "Revenue reached $391.035 billion in fiscal year 2024 [C99].",
                "sections": [],
                "calculation_explanation": None,
                "cited_claim_ids": ["claim-1"],
                "citation_markers": ["[C99]"],
                "limitations_disclosed": [],
                "warnings": [],
            }

        if self.mode == "unsupported_claim":
            return {
                "summary": "Apple plans to acquire a space exploration company in 2025.",  # Unsupported
                "detailed_answer": "Apple plans to acquire a space exploration company next year.",
                "sections": [],
                "calculation_explanation": None,
                "cited_claim_ids": ["unsupported-claim-999"],
                "citation_markers": [],
                "limitations_disclosed": [],
                "warnings": ["Speculative forward statement"],
            }

        # Default valid response
        return {
            "summary": "Apple's total net sales for FY2024 was $391,035 million ($391.04B), increasing 2.02% from FY2023 [C1].",
            "detailed_answer": (
                "Apple Inc. reported total net sales of $391,035 million for fiscal year 2024, compared to "
                "$383,285 million in fiscal year 2023 [C1]. This represents a year-over-year revenue increase of "
                "+2.02% [C1]."
            ),
            "sections": [
                {
                    "heading": "Financial Performance",
                    "content": "Total net sales reached $391,035 million in FY2024 [C1].",
                    "claim_ids": ["claim-1"],
                    "citation_markers": ["[C1]"],
                }
            ],
            "calculation_explanation": "Revenue Growth = (($391,035M - $383,285M) / $383,285M) * 100 = +2.02%",
            "cited_claim_ids": ["claim-1"],
            "citation_markers": ["[C1]"],
            "limitations_disclosed": [],
            "warnings": [],
        }
