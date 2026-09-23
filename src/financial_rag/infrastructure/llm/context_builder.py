"""Deterministic Context Builder packaging AnswerPackage into structured, budgeted context blocks."""

from financial_rag.domain.entities.reasoning import AnswerPackage
from financial_rag.domain.interfaces.answer import ContextBuilderProtocol


class DeterministicContextBuilder(ContextBuilderProtocol):
    """Packages verified Phase 3 AnswerPackage into cleanly delimited, budgeted context sections."""

    def build_context(
        self,
        answer_package: AnswerPackage,
        max_tokens: int = 4000,
    ) -> str:
        """Construct structured context string adhering to token budget."""
        char_budget = max_tokens * 4

        sections: list[str] = []

        # 1. Question Section
        sections.append(f"<QUESTION>\n{answer_package.raw_query}\n</QUESTION>")

        # 2. Answerability Section
        sections.append(
            f"<ANSWERABILITY>\n"
            f"Status: {answer_package.answerability.value}\n"
            f"Rationale: {answer_package.answerability_rationale}\n"
            f"</ANSWERABILITY>"
        )

        # 3. Verified Facts Section
        facts_lines = []
        for _idx, fact in enumerate(answer_package.facts, start=1):
            facts_lines.append(
                f"- Fact [{fact.fact_id}]: {fact.company} {fact.metric} ({fact.period.label}) = "
                f"{fact.value.display_value} (Numeric: {fact.value.numeric_value} {fact.value.unit}) | "
                f"Source: Doc '{fact.document_id}' Page {fact.page_number}"
            )
        if facts_lines:
            sections.append("<VERIFIED_FACTS>\n" + "\n".join(facts_lines) + "\n</VERIFIED_FACTS>")

        # 4. Calculations Section
        calc_lines = []
        for calc in answer_package.calculations:
            calc_lines.append(
                f"- Calculation [{calc.calculation_id}]: Operation '{calc.operation.value}' | "
                f"Formula: {calc.formula} | Result: {calc.display_result} (Success: {calc.success})"
            )
        if calc_lines:
            sections.append("<CALCULATIONS>\n" + "\n".join(calc_lines) + "\n</CALCULATIONS>")

        # 5. Verified Claims Section
        claim_lines = []
        for claim in answer_package.claims:
            claim_lines.append(
                f"- Claim [{claim.claim_id}] ({claim.claim_type}): {claim.text} "
                f"(Grounded: {claim.is_grounded})"
            )
        if claim_lines:
            sections.append("<CLAIMS>\n" + "\n".join(claim_lines) + "\n</CLAIMS>")

        # 6. Citation Map Section
        citation_lines = []
        for idx, cit in enumerate(answer_package.citations, start=1):
            marker = f"[C{idx}]"
            citation_lines.append(
                f"{marker} -> ID: {cit.citation_id} | Document: {cit.document_id} | "
                f"Page: {cit.page_number} | Section: {cit.section_path} | "
                f'Excerpt: "{cit.source_excerpt}"'
            )
        if citation_lines:
            sections.append("<CITATION_MAP>\n" + "\n".join(citation_lines) + "\n</CITATION_MAP>")

        # 7. Conflicts & Warnings Section
        warning_lines = []
        for conflict in answer_package.conflicts:
            warning_lines.append(
                f"- Conflict: {conflict.metric} ({conflict.period}) - {conflict.difference_description} "
                f"(Resolved: {conflict.resolved})"
            )
        for warn in answer_package.warnings:
            warning_lines.append(f"- Warning: {warn}")
        if warning_lines:
            sections.append("<WARNINGS>\n" + "\n".join(warning_lines) + "\n</WARNINGS>")

        # 8. Source Evidence Excerpts (Budget-permitting)
        evidence_lines = []
        for _idx, ev in enumerate(answer_package.evidence, start=1):
            clean_content = ev.content.strip().replace("\n", " ")
            if len(clean_content) > 300:
                clean_content = clean_content[:300] + "..."
            evidence_lines.append(
                f'- Evidence [{ev.chunk_id}] (Page {ev.page_number}, {ev.chunk_type.value}): "{clean_content}"'
            )
        if evidence_lines:
            sections.append(
                "<SOURCE_EVIDENCE>\n" + "\n".join(evidence_lines) + "\n</SOURCE_EVIDENCE>"
            )

        # Assemble and budget
        full_context = "\n\n".join(sections)
        if len(full_context) <= char_budget:
            return full_context

        # If exceeding budget, truncate source evidence first
        budget_remaining = char_budget
        truncated_sections = []
        for sec in sections:
            if len(sec) <= budget_remaining:
                truncated_sections.append(sec)
                budget_remaining -= len(sec) + 2
            else:
                if budget_remaining > 100:
                    truncated_sections.append(
                        sec[:budget_remaining] + "\n...[TRUNCATED]</SOURCE_EVIDENCE>"
                    )
                break

        return "\n\n".join(truncated_sections)
