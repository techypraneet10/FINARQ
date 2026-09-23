"""Deterministic Answerability Gate evaluating AnswerPackage and enforcing safe non-LLM responses for non-answerable states."""

from uuid import uuid4

from financial_rag.domain.entities.answer import AnswerRequest, AnswerResponse, AnswerStatus
from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    AnswerPackage,
    GroundingStatus,
)
from financial_rag.domain.interfaces.answer import AnswerabilityGateProtocol


class DeterministicAnswerabilityGate(AnswerabilityGateProtocol):
    """Inspects AnswerPackage answerability and intercepts unanswerable or unsafe queries."""

    def evaluate_gate(
        self,
        answer_package: AnswerPackage,
        request: AnswerRequest,
    ) -> AnswerResponse | None:
        """Return deterministic AnswerResponse if question is non-answerable, or None to proceed."""
        status = answer_package.answerability
        grounding_status = (
            answer_package.grounding_validation.status
            if answer_package.grounding_validation
            else GroundingStatus.GROUNDED
        )

        # 1. INSUFFICIENT_EVIDENCE
        if status == AnswerabilityStatus.INSUFFICIENT_EVIDENCE:
            missing_str = (
                ", ".join(answer_package.missing_facts)
                if answer_package.missing_facts
                else "metrics/periods requested"
            )
            text = (
                f"The available financial documents do not provide sufficient evidence to answer this inquiry. "
                f"Specifically, the following required information was not found in the indexed corpus: {missing_str}. "
                f"Rationale: {answer_package.answerability_rationale}"
            )
            return AnswerResponse(
                answer_id=uuid4(),
                query_id=uuid4(),
                status=AnswerStatus.INSUFFICIENT_EVIDENCE,
                answer_text=text,
                claims=answer_package.claims,
                citations=answer_package.citations,
                calculations=answer_package.calculations,
                facts=answer_package.facts,
                reasoning_plan=answer_package.reasoning_plan,
                grounding_status=grounding_status,
                confidence_score=0.0,
                warnings=answer_package.warnings,
                metadata={"gate_intercepted": True, "answerability": status.value},
            )

        # 2. CONFLICTING_EVIDENCE
        if status == AnswerabilityStatus.CONFLICTING_EVIDENCE:
            conflict_descriptions = [
                f"- {c.metric} ({c.period}): {c.difference_description}"
                for c in answer_package.conflicts
            ]
            conflicts_str = (
                "\n".join(conflict_descriptions)
                if conflict_descriptions
                else "Conflicting metric values detected."
            )
            text = (
                f"The available financial documents contain conflicting evidence for the requested inquiry:\n"
                f"{conflicts_str}\n\n"
                f"The system cannot provide a definitive single answer without resolving the underlying discrepancy. "
                f"Rationale: {answer_package.answerability_rationale}"
            )
            return AnswerResponse(
                answer_id=uuid4(),
                query_id=uuid4(),
                status=AnswerStatus.CONFLICTING_EVIDENCE,
                answer_text=text,
                claims=answer_package.claims,
                citations=answer_package.citations,
                calculations=answer_package.calculations,
                facts=answer_package.facts,
                reasoning_plan=answer_package.reasoning_plan,
                grounding_status=grounding_status,
                confidence_score=0.2,
                warnings=[
                    *answer_package.warnings,
                    *[f"Conflict: {c.difference_description}" for c in answer_package.conflicts],
                ],
                metadata={"gate_intercepted": True, "answerability": status.value},
            )

        # 3. CALCULATION_FAILED
        if status == AnswerabilityStatus.CALCULATION_FAILED:
            failed_calcs = [c for c in answer_package.calculations if not c.success]
            err_msg = (
                failed_calcs[0].error_message if failed_calcs else "Arithmetic calculation failed"
            )
            text = (
                f"A deterministic financial calculation could not be completed successfully. "
                f"Details: {err_msg}. "
                f"Rationale: {answer_package.answerability_rationale}"
            )
            return AnswerResponse(
                answer_id=uuid4(),
                query_id=uuid4(),
                status=AnswerStatus.CALCULATION_FAILED,
                answer_text=text,
                claims=answer_package.claims,
                citations=answer_package.citations,
                calculations=answer_package.calculations,
                facts=answer_package.facts,
                reasoning_plan=answer_package.reasoning_plan,
                grounding_status=grounding_status,
                confidence_score=0.0,
                warnings=[*answer_package.warnings, f"Calculation failure: {err_msg}"],
                metadata={"gate_intercepted": True, "answerability": status.value},
            )

        # 4. GROUNDING_FAILED
        if status == AnswerabilityStatus.GROUNDING_FAILED:
            text = (
                f"Answer synthesis cannot proceed because the extracted claims failed grounding validation "
                f"against the source documents. Rationale: {answer_package.answerability_rationale}"
            )
            return AnswerResponse(
                answer_id=uuid4(),
                query_id=uuid4(),
                status=AnswerStatus.GROUNDING_FAILED,
                answer_text=text,
                claims=answer_package.claims,
                citations=answer_package.citations,
                calculations=answer_package.calculations,
                facts=answer_package.facts,
                reasoning_plan=answer_package.reasoning_plan,
                grounding_status=grounding_status,
                confidence_score=0.0,
                warnings=[
                    *answer_package.warnings,
                    "Grounding validation failed for source claims",
                ],
                metadata={"gate_intercepted": True, "answerability": status.value},
            )

        # 5. INVALID_QUERY
        if status == AnswerabilityStatus.INVALID_QUERY:
            text = (
                f"The financial query is invalid, ambiguous, or underspecified (e.g., missing specific company, fiscal year, or metric). "
                f"Rationale: {answer_package.answerability_rationale}"
            )
            return AnswerResponse(
                answer_id=uuid4(),
                query_id=uuid4(),
                status=AnswerStatus.INVALID_QUERY,
                answer_text=text,
                claims=answer_package.claims,
                citations=answer_package.citations,
                calculations=answer_package.calculations,
                facts=answer_package.facts,
                reasoning_plan=answer_package.reasoning_plan,
                grounding_status=grounding_status,
                confidence_score=0.0,
                warnings=answer_package.warnings,
                metadata={"gate_intercepted": True, "answerability": status.value},
            )

        # For ANSWERABLE and PARTIALLY_ANSWERABLE, proceed to LLM synthesis
        return None
