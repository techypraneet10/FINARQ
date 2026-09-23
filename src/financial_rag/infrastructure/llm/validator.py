"""Deterministic 8-stage Answer Validator ensuring strict schema, citation, and numerical fidelity."""

import re
from decimal import Decimal

from financial_rag.domain.entities.answer import (
    AnswerRequest,
    LLMAnswerOutput,
    ResponseStyle,
    ValidationFailure,
    ValidationResult,
)
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    GroundingStatus,
)
from financial_rag.domain.interfaces.answer import AnswerValidatorProtocol


class DeterministicAnswerValidator(AnswerValidatorProtocol):
    """Audits LLM synthesis outputs across 8 deterministic safety and fidelity stages."""

    def __init__(self, numerical_tolerance_pct: float = 0.5) -> None:
        self.numerical_tolerance_pct = numerical_tolerance_pct

    def validate_answer(
        self,
        llm_output: LLMAnswerOutput,
        answer_package: AnswerPackage,
        request: AnswerRequest,
    ) -> ValidationResult:
        """Execute full 8-stage validation audit."""
        failures: list[ValidationFailure] = []
        num_discrepancies: list[str] = []
        invalid_citations: list[str] = []
        unsupported_claims: list[str] = []

        # Stage 1: Schema & Completeness Validation
        if not llm_output.summary or not llm_output.summary.strip():
            failures.append(
                ValidationFailure(
                    stage="schema",
                    code="EMPTY_SUMMARY",
                    message="LLM output summary is empty.",
                    severity="retryable",
                )
            )
        if not llm_output.detailed_answer or not llm_output.detailed_answer.strip():
            failures.append(
                ValidationFailure(
                    stage="schema",
                    code="EMPTY_DETAILED_ANSWER",
                    message="LLM output detailed_answer is empty.",
                    severity="retryable",
                )
            )

        # Stage 2: Citation Marker Validation
        valid_citation_markers = {f"[C{i}]" for i in range(1, len(answer_package.citations) + 1)}
        extracted_markers = set(
            re.findall(r"\[C\d+\]", llm_output.detailed_answer + " " + llm_output.summary)
        )
        for section in llm_output.sections:
            extracted_markers.update(re.findall(r"\[C\d+\]", section.content))

        for marker in extracted_markers:
            if marker not in valid_citation_markers:
                invalid_citations.append(marker)
                failures.append(
                    ValidationFailure(
                        stage="citation_markers",
                        code="UNKNOWN_CITATION_MARKER",
                        message=f"LLM output used unknown citation marker '{marker}' (Valid: {sorted(valid_citation_markers)}).",
                        severity="retryable",
                        details={"marker": marker, "valid_markers": list(valid_citation_markers)},
                    )
                )

        # Stage 3: Claim Reference Validation
        valid_claim_ids = {c.claim_id for c in answer_package.claims}
        for claim_id in llm_output.cited_claim_ids:
            if valid_claim_ids and claim_id not in valid_claim_ids:
                unsupported_claims.append(claim_id)
                failures.append(
                    ValidationFailure(
                        stage="claim_references",
                        code="UNKNOWN_CLAIM_ID",
                        message=f"LLM output referenced unknown claim ID '{claim_id}'.",
                        severity="warning",
                        details={"claim_id": claim_id},
                    )
                )

        # Stage 4: Numerical Fidelity Validation
        verified_numbers = self._collect_verified_numbers(answer_package)
        text_numbers = self._extract_numbers_from_text(
            llm_output.summary + " " + llm_output.detailed_answer
        )

        for text_num in text_numbers:
            # Check if this number is accounted for in verified numbers, fiscal years, or common structural integers
            if not self._is_number_verified(text_num, verified_numbers):
                num_discrepancies.append(str(text_num))
                failures.append(
                    ValidationFailure(
                        stage="numerical_fidelity",
                        code="UNVERIFIED_NUMBER",
                        message=f"Generated text contains unverified number '{text_num}'.",
                        severity="retryable",
                        details={"number": str(text_num)},
                    )
                )

        # Stage 5: Grounding Consistency Validation
        if (
            answer_package.grounding_validation is not None
            and answer_package.grounding_validation.status == GroundingStatus.PARTIALLY_GROUNDED
            and not llm_output.limitations_disclosed
        ):
            failures.append(
                ValidationFailure(
                    stage="grounding_consistency",
                    code="UNDISCLOSED_PARTIAL_GROUNDING",
                    message="AnswerPackage is PARTIALLY_GROUNDED but LLM output disclosed no limitations.",
                    severity="warning",
                )
            )

        # Stage 6: Answerability Consistency Validation
        if (
            answer_package.answerability == AnswerabilityStatus.PARTIALLY_ANSWERABLE
            and not llm_output.limitations_disclosed
        ):
            failures.append(
                ValidationFailure(
                    stage="answerability_consistency",
                    code="UNDISCLOSED_PARTIAL_ANSWER",
                    message="Query is PARTIALLY_ANSWERABLE but LLM output failed to disclose partial status.",
                    severity="warning",
                )
            )

        # Stage 7: Unsupported Content Detection (Speculation / Hallucination Keywords)
        speculative_patterns = [
            r"\bI predict\b",
            r"\bI believe\b",
            r"\bguaranteed to\b",
            r"\bdefinitely will\b",
            r"\bsecretly\b",
        ]
        combined_text = (llm_output.summary + " " + llm_output.detailed_answer).lower()
        for pat in speculative_patterns:
            if re.search(pat, combined_text):
                failures.append(
                    ValidationFailure(
                        stage="unsupported_content",
                        code="SPECULATIVE_LANGUAGE_DETECTED",
                        message=f"Generated text contains speculative phrase matching '{pat}'.",
                        severity="warning",
                    )
                )

        # Stage 8: Length / Style Validation
        if (
            request.response_style == ResponseStyle.CONCISE
            and len(llm_output.detailed_answer) > 1500
        ):
            failures.append(
                ValidationFailure(
                    stage="style_compliance",
                    code="CONCISE_LENGTH_EXCEEDED",
                    message=f"Concise response exceeded length limit ({len(llm_output.detailed_answer)} chars > 1500).",
                    severity="warning",
                )
            )

        # Determine overall validity: any fatal or retryable failures cause valid=False
        has_critical_failures = any(f.severity in ("fatal", "retryable") for f in failures)
        is_valid = not has_critical_failures
        retry_recommended = any(f.severity == "retryable" for f in failures)

        return ValidationResult(
            valid=is_valid,
            failures=failures,
            numerical_discrepancies=num_discrepancies,
            invalid_citations=invalid_citations,
            unsupported_claims=unsupported_claims,
            retry_recommended=retry_recommended,
        )

    def _collect_verified_numbers(self, answer_package: AnswerPackage) -> set[Decimal]:
        """Harvest all valid numbers from facts, calculations, and metadata."""
        numbers: set[Decimal] = set()

        # Structural numbers (years, items, 0, 1, 2, 100)
        for y in range(2000, 2040):
            numbers.add(Decimal(str(y)))
        for common_int in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 100]:
            numbers.add(Decimal(str(common_int)))

        # From facts
        for fact in answer_package.facts:
            numbers.add(fact.value.numeric_value)
            numbers.add(fact.value.unscaled_value)
            if fact.period.fiscal_year:
                numbers.add(Decimal(str(fact.period.fiscal_year)))

        # From calculations
        for calc in answer_package.calculations:
            numbers.add(calc.raw_result)
            numbers.add(calc.rounded_result)
            for inp in calc.inputs:
                numbers.add(inp.value)
            for fn in self._extract_numbers_from_text(calc.formula):
                numbers.add(fn)

        # From claims
        for claim in answer_package.claims:
            for cn in self._extract_numbers_from_text(claim.text):
                numbers.add(cn)

        # From citations
        for cit in answer_package.citations:
            numbers.add(Decimal(str(cit.page_number)))
            for p in cit.page_numbers:
                numbers.add(Decimal(str(p)))

        return numbers

    def _extract_numbers_from_text(self, text: str) -> list[Decimal]:
        """Extract candidate financial numbers from text."""
        cleaned = text.replace(",", "")
        # Match monetary or general numbers (e.g., 391035, 391.035, 2.02, 180683)
        matches = re.findall(r"(?<![C\w])[-+]?\d+(?:\.\d+)?%?", cleaned)
        results: list[Decimal] = []
        for m in matches:
            val_str = m.rstrip("%")
            try:
                dec = Decimal(val_str)
                # Ignore very small indices (0-10) already accounted for
                results.append(dec)
            except Exception:
                continue
        return results

    def _is_number_verified(self, num: Decimal, verified_numbers: set[Decimal]) -> bool:
        """Check if number exists in verified set or within financial tolerance."""
        if num in verified_numbers:
            return True

        # Check tolerance matching for financial quantities (e.g. 391.04 vs 391.035)
        for v in verified_numbers:
            if v == Decimal("0"):
                continue
            # For values >= 10, allow minor rounding diff of <= 0.05
            if abs(v) >= Decimal("10") and abs(num - v) <= Decimal("0.05"):
                return True
            # Scaled billions / millions checks (e.g., 391.04 billion vs 391035 million) - only for substantial financial values
            if abs(v) >= Decimal("1000") and abs((num * Decimal("1000")) - v) / abs(v) <= Decimal(
                "0.01"
            ):
                return True
            if abs(v) >= Decimal("1000") and abs((num * Decimal("1000000")) - v) / abs(
                v
            ) <= Decimal("0.01"):
                return True
            if abs(num) >= Decimal("1000") and abs((v * Decimal("1000")) - num) / abs(
                num
            ) <= Decimal("0.01"):
                return True

        return False
