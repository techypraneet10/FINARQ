from typing import Any

from financial_rag.domain.entities.answer import AnswerRequest
from financial_rag.domain.entities.reasoning import AnswerPackage
from financial_rag.domain.interfaces.answer import PromptBuilderProtocol
from financial_rag.infrastructure.llm.prompts.v1 import (
    PROMPT_VERSION_V1,
    SYSTEM_INSTRUCTION_V1,
    build_correction_prompt_v1,
    build_user_prompt_v1,
)

PROMPT_VERSION = PROMPT_VERSION_V1
SYSTEM_INSTRUCTION = SYSTEM_INSTRUCTION_V1


class VersionedPromptBuilder(PromptBuilderProtocol):
    """Builds versioned, style-customized prompts with explicit boundary delimiters."""

    def __init__(self, prompt_version: str = PROMPT_VERSION) -> None:
        self.prompt_version = prompt_version

    def build_prompt(
        self,
        request: AnswerRequest,
        context: str,
        answer_package: AnswerPackage,
    ) -> tuple[str, str, str]:
        """Construct user prompt, system instructions, and return prompt version."""
        user_prompt = build_user_prompt_v1(
            query=request.query,
            context=context,
            style=request.response_style,
            include_citations=request.include_citations,
            custom_instructions=request.custom_instructions,
        )
        return user_prompt, SYSTEM_INSTRUCTION_V1, self.prompt_version

    def build_correction_prompt(
        self,
        base_prompt: str,
        failures: list[Any],
    ) -> str:
        """Append validation failure corrections to prompt."""
        failure_messages = [getattr(f, "message", str(f)) for f in failures]
        return build_correction_prompt_v1(base_prompt=base_prompt, failures=failure_messages)
