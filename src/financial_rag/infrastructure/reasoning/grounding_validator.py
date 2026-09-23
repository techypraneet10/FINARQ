"""Grounding validation engine auditing unbroken evidence-to-claim reasoning chains."""

from typing import Any

from financial_rag.domain.entities.reasoning import (
    CalculationResult,
    Citation,
    Claim,
    EvidenceConflict,
    FinancialFact,
    GroundingStatus,
    GroundingValidationResult,
)
from financial_rag.domain.interfaces.reasoning import GroundingValidatorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.grounding_validator")


class DeterministicGroundingValidator(GroundingValidatorProtocol):
    """Validates that all factual and calculated claims have verified provenance and calculation grounding."""

    def validate(
        self,
        claims: list[Claim],
        facts: list[FinancialFact],
        calculations: list[CalculationResult],
        citations: list[Citation],
        conflicts: list[EvidenceConflict],
    ) -> GroundingValidationResult:
        """Execute full grounding audit and return GroundingValidationResult."""
        total_claims = len(claims)
        if total_claims == 0:
            return GroundingValidationResult(
                status=GroundingStatus.GROUNDED,
                total_claims=0,
                grounded_claims=0,
                ungrounded_claims=0,
                conflicting_claims=0,
                unverified_citations=0,
                details=[],
                validation_passed=True,
            )

        calcs_by_id = {c.calculation_id: c for c in calculations}
        citations_by_claim_id: dict[str, list[Citation]] = {}

        for cit in citations:
            citations_by_claim_id.setdefault(cit.claim_id, []).append(cit)

        grounded_count = 0
        ungrounded_count = 0
        conflicting_count = 0
        unverified_cit_count = sum(1 for c in citations if not c.verified)
        details: list[dict[str, Any]] = []

        unresolved_conflict_facts = set()
        for conf in conflicts:
            if not conf.resolved:
                for f in conf.conflicting_facts:
                    unresolved_conflict_facts.add(f.fact_id)

        for claim in claims:
            claim_citations = citations_by_claim_id.get(claim.claim_id, [])
            verified_cits = [c for c in claim_citations if c.verified]

            # Check if claim involves unresolved conflicts
            has_conflict = any(fid in unresolved_conflict_facts for fid in claim.source_fact_ids)
            if has_conflict:
                conflicting_count += 1
                details.append(
                    {
                        "claim_id": claim.claim_id,
                        "text": claim.text,
                        "status": "conflicting",
                        "reason": "Claim references unresolved conflicting facts across evidence sources.",
                    }
                )
                continue

            # Check calculation grounding if claim is calculated
            if claim.claim_type == "calculated":
                if not claim.calculation_ids:
                    ungrounded_count += 1
                    details.append(
                        {
                            "claim_id": claim.claim_id,
                            "text": claim.text,
                            "status": "ungrounded",
                            "reason": "Calculated claim is missing associated calculation result ID.",
                        }
                    )
                    continue

                calc_ok = True
                for calc_id in claim.calculation_ids:
                    calc = calcs_by_id.get(calc_id)
                    if not calc or not calc.success:
                        calc_ok = False
                        break

                if not calc_ok:
                    ungrounded_count += 1
                    details.append(
                        {
                            "claim_id": claim.claim_id,
                            "text": claim.text,
                            "status": "ungrounded",
                            "reason": "Underlying calculation failed or was missing.",
                        }
                    )
                    continue

            # Check evidence grounding: claim must have at least one verified citation
            if not verified_cits:
                ungrounded_count += 1
                details.append(
                    {
                        "claim_id": claim.claim_id,
                        "text": claim.text,
                        "status": "ungrounded",
                        "reason": "Claim lacks verified citations pointing to active evidence.",
                    }
                )
            else:
                grounded_count += 1
                details.append(
                    {
                        "claim_id": claim.claim_id,
                        "text": claim.text,
                        "status": "grounded",
                        "citations_count": len(verified_cits),
                    }
                )

        # Determine overall grounding status
        if conflicting_count > 0:
            status = GroundingStatus.CONFLICTING
            passed = False
        elif ungrounded_count == 0:
            status = GroundingStatus.GROUNDED
            passed = True
        elif grounded_count > 0:
            status = GroundingStatus.PARTIALLY_GROUNDED
            passed = False
        else:
            status = GroundingStatus.UNGROUNDED
            passed = False

        logger.info(
            f"Grounding validation completed: status={status.value} "
            f"({grounded_count}/{total_claims} grounded, {ungrounded_count} ungrounded, {conflicting_count} conflicting)"
        )

        return GroundingValidationResult(
            status=status,
            total_claims=total_claims,
            grounded_claims=grounded_count,
            ungrounded_claims=ungrounded_count,
            conflicting_claims=conflicting_count,
            unverified_citations=unverified_cit_count,
            details=details,
            validation_passed=passed,
        )
