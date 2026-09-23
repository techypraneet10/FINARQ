"""Deterministic Response Renderer formatting validated structured answers into human-readable outputs."""

from financial_rag.domain.entities.answer import (
    AnswerRequest,
    LLMAnswerOutput,
    ResponseStyle,
    ValidationResult,
)
from financial_rag.domain.entities.reasoning import AnswerPackage
from financial_rag.domain.interfaces.answer import ResponseRendererProtocol


class DeterministicResponseRenderer(ResponseRendererProtocol):
    """Renders validated structured answers and safe fallbacks according to requested presentation styles."""

    def render_response(
        self,
        llm_output: LLMAnswerOutput,
        answer_package: AnswerPackage,
        request: AnswerRequest,
        validation_result: ValidationResult,
    ) -> str:
        """Render final formatted markdown string."""
        parts: list[str] = []

        # 1. Main Answer Body
        if request.response_style == ResponseStyle.CONCISE:
            parts.append(llm_output.summary)
            if llm_output.calculation_explanation:
                parts.append(f"\n*Calculation:* `{llm_output.calculation_explanation}`")
        elif request.response_style == ResponseStyle.DETAILED:
            parts.append(f"### Executive Summary\n{llm_output.summary}\n")
            if llm_output.sections:
                for section in llm_output.sections:
                    parts.append(f"#### {section.heading}\n{section.content}\n")
            else:
                parts.append(f"### Details\n{llm_output.detailed_answer}\n")
            if llm_output.calculation_explanation:
                parts.append(f"### Calculation Breakdown\n`{llm_output.calculation_explanation}`\n")
        elif request.response_style == ResponseStyle.ANALYTICAL:
            parts.append(f"### Analysis\n{llm_output.detailed_answer}\n")
            if llm_output.calculation_explanation:
                parts.append(
                    f"**Deterministic Formula:**\n```\n{llm_output.calculation_explanation}\n```\n"
                )
            if llm_output.limitations_disclosed:
                parts.append(
                    "### Limitations & Data Scope\n"
                    + "\n".join(f"- {lim}" for lim in llm_output.limitations_disclosed)
                    + "\n"
                )
        else:  # STANDARD
            parts.append(llm_output.detailed_answer)
            if llm_output.calculation_explanation:
                parts.append(f"\n**Calculation:** `{llm_output.calculation_explanation}`")

        # 2. Citations Footer (if requested)
        if request.include_citations and answer_package.citations:
            citation_lines = []
            for idx, cit in enumerate(answer_package.citations, start=1):
                marker = f"[C{idx}]"
                sec_path = f", Section: {cit.section_path}" if cit.section_path else ""
                citation_lines.append(
                    f"- **{marker}**: Document `{cit.document_id}`, Page {cit.page_number}{sec_path}"
                )
            parts.append("\n\n### Sources & Citations\n" + "\n".join(citation_lines))

        # 3. Warnings / Caveats
        if answer_package.warnings:
            parts.append("\n\n> **Note:** " + " | ".join(answer_package.warnings))

        return "\n".join(parts).strip()

    def render_deterministic_fallback(
        self,
        answer_package: AnswerPackage,
        request: AnswerRequest,
        reason: str,
    ) -> str:
        """Synthesize a safe, 100% grounded response constructed strictly from verified facts and calculations."""
        parts: list[str] = []

        # Header warning
        parts.append(f"> *[Fallback Answer - {reason}]*\n")

        # 1. Synthesize claims from verified facts and calculations
        if answer_package.claims:
            claims_text = " ".join(
                f"{c.text} [C{i}]" for i, c in enumerate(answer_package.claims, start=1)
            )
            parts.append(claims_text)
        elif answer_package.facts:
            facts_text = " ".join(
                f"{f.company} {f.metric} for {f.period.label} was {f.value.display_value}."
                for f in answer_package.facts
            )
            parts.append(facts_text)
        else:
            parts.append(
                "No verified financial claims could be extracted from the retrieved documents."
            )

        # 2. Calculation summary
        for calc in answer_package.calculations:
            if calc.success:
                parts.append(
                    f"\n**Verified Calculation:** `{calc.formula}` = **{calc.display_result}**"
                )

        # 3. Citations
        if request.include_citations and answer_package.citations:
            citation_lines = []
            for idx, cit in enumerate(answer_package.citations, start=1):
                marker = f"[C{idx}]"
                sec = f", Section: {cit.section_path}" if cit.section_path else ""
                citation_lines.append(
                    f"- **{marker}**: Document `{cit.document_id}`, Page {cit.page_number}{sec}"
                )
            parts.append("\n\n### Sources & Citations\n" + "\n".join(citation_lines))

        return "\n".join(parts).strip()
