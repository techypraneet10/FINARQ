"""Deterministic claim construction engine generating verifiable claims from facts and calculations."""

from uuid import uuid4

from financial_rag.domain.entities.reasoning import (
    CalculationResult,
    Claim,
    FinancialFact,
    ReasoningOperation,
    ReasoningPlan,
)
from financial_rag.domain.interfaces.reasoning import ClaimBuilderProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.claim_builder")


class DeterministicClaimBuilder(ClaimBuilderProtocol):
    """Constructs structured, machine-verifiable factual and calculated claims."""

    def build_claims(
        self,
        plan: ReasoningPlan,
        facts: list[FinancialFact],
        calculations: list[CalculationResult],
    ) -> list[Claim]:
        """Build atomic claims from extracted facts and calculation results."""
        claims: list[Claim] = []

        # 1. Claims for individual direct facts
        for fact in facts:
            company_str = f"{fact.company} " if fact.company and fact.company != "Company" else ""
            claim_text = (
                f"{company_str}{fact.metric} for {fact.period.label} "
                f"was {fact.value.display_value}."
            )
            claims.append(
                Claim(
                    claim_id=str(uuid4()),
                    text=claim_text,
                    claim_type="direct_fact",
                    source_fact_ids=[fact.fact_id],
                    calculation_ids=[],
                    reasoning_step_ids=[1],
                    confidence=fact.confidence,
                    is_grounded=True,
                )
            )

        # 2. Claims for calculation results
        for calc in calculations:
            if not calc.success:
                continue

            op = calc.operation
            if op in (ReasoningOperation.PERCENTAGE_CHANGE, ReasoningOperation.GROWTH_RATE):
                if len(calc.inputs) >= 2:
                    claim_text = (
                        f"Growth from {calc.inputs[0].name} to {calc.inputs[1].name} "
                        f"was {calc.display_result}."
                    )
                else:
                    claim_text = f"Growth rate was {calc.display_result}."
            elif op == ReasoningOperation.DIFFERENCE:
                if len(calc.inputs) >= 2:
                    claim_text = (
                        f"Difference between {calc.inputs[0].name} and {calc.inputs[1].name} "
                        f"was {calc.display_result}."
                    )
                else:
                    claim_text = f"Difference was {calc.display_result}."
            elif op == ReasoningOperation.RATIO:
                if len(calc.inputs) >= 2:
                    claim_text = (
                        f"Ratio of {calc.inputs[0].name} to {calc.inputs[1].name} "
                        f"was {calc.display_result}."
                    )
                else:
                    claim_text = f"Ratio was {calc.display_result}."
            elif op == ReasoningOperation.SUM:
                claim_text = f"Total sum across periods was {calc.display_result}."
            elif op == ReasoningOperation.AVERAGE:
                claim_text = f"Average across periods was {calc.display_result}."
            elif op in (ReasoningOperation.TREND, ReasoningOperation.MULTI_PERIOD_COMPARISON):
                claim_text = f"Multi-period analysis: {calc.display_result}."
            else:
                claim_text = f"Result for {op.value}: {calc.display_result}."

            claims.append(
                Claim(
                    claim_id=str(uuid4()),
                    text=claim_text,
                    claim_type="calculated",
                    source_fact_ids=calc.input_fact_ids,
                    calculation_ids=[calc.calculation_id],
                    reasoning_step_ids=[2],
                    confidence=0.99,
                    is_grounded=len(calc.input_fact_ids) > 0,
                )
            )

        logger.info(f"Constructed {len(claims)} atomic claims")
        return claims
