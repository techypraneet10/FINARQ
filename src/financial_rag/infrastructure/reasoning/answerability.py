"""Answerability classification state machine evaluating evidence sufficiency and validity."""

from typing import ClassVar

from financial_rag.domain.entities.reasoning import (
    AnswerabilityStatus,
    CalculationResult,
    EvidenceConflict,
    FinancialFact,
    GroundingStatus,
    GroundingValidationResult,
    ReasoningPlan,
)
from financial_rag.domain.interfaces.reasoning import AnswerabilityEvaluatorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.answerability")


class DeterministicAnswerabilityEvaluator(AnswerabilityEvaluatorProtocol):
    """Evaluates answerability state, missing fact identification, and rationale."""

    SYNONYM_GROUPS: ClassVar[list[set[str]]] = [
        {
            "revenue",
            "revenues",
            "sales",
            "net sales",
            "total net sales",
            "total revenue",
            "total revenues",
            "turnover",
        },
        {"net income", "net earnings", "net profit", "consolidated net income", "net loss"},
        {"operating income", "operating profit", "income from operations", "operating earnings"},
        {"gross margin", "gross profit", "gross income"},
        {"operating expenses", "total operating expenses", "opex"},
        {"cost of sales", "cost of revenue", "cost of goods sold", "cogs"},
    ]

    def _matches_synonym(self, metric1: str, metric2: str) -> bool:
        m1 = metric1.lower()
        m2 = metric2.lower()
        if m1 in m2 or m2 in m1:
            return True
        for group in self.SYNONYM_GROUPS:
            if any(term in m1 for term in group) and any(term in m2 for term in group):
                return True
        return False

    def evaluate(
        self,
        plan: ReasoningPlan,
        facts: list[FinancialFact],
        calculations: list[CalculationResult],
        conflicts: list[EvidenceConflict],
        grounding: GroundingValidationResult,
    ) -> tuple[AnswerabilityStatus, str, list[str]]:
        """Determine AnswerabilityStatus, rationale description, and missing required facts."""
        missing_facts: list[str] = []

        # 1. Evaluate fact coverage against required plan keys
        for req_key in plan.required_fact_keys:
            # req_key is e.g. "revenue_2024" or "revenue"
            matched = False
            for fact in facts:
                fact_metric = fact.metric.lower()
                fact_period = fact.period.label.lower()
                fact_year = str(fact.period.fiscal_year) if fact.period.fiscal_year else ""

                if "_" in req_key:
                    parts = req_key.split("_", 1)
                    req_metric, req_period = parts[0], parts[1]
                    if self._matches_synonym(req_metric, fact_metric) and (
                        req_period in fact_period or (fact_year and req_period in fact_year)
                    ):
                        matched = True
                        break
                else:
                    if self._matches_synonym(req_key, fact_metric):
                        matched = True
                        break
            if not matched:
                missing_facts.append(req_key)

        # 2. Case: Zero facts extracted
        if not facts:
            return (
                AnswerabilityStatus.INSUFFICIENT_EVIDENCE,
                "No relevant financial facts could be extracted from retrieved document evidence.",
                plan.required_fact_keys or ["target_metric"],
            )

        # 3. Case: Unresolved conflicting evidence
        unresolved_conflicts = [c for c in conflicts if not c.resolved]
        if unresolved_conflicts:
            conflict_descs = [c.difference_description for c in unresolved_conflicts]
            return (
                AnswerabilityStatus.CONFLICTING_EVIDENCE,
                f"Irreconcilable factual discrepancies found: {'; '.join(conflict_descs)}",
                missing_facts,
            )

        # 4. Case: Calculation failures
        failed_calcs = [c for c in calculations if not c.success]
        if failed_calcs:
            reasons = [c.error_message or "Unknown calculation error" for c in failed_calcs]
            if "division by zero" in reasons[0].lower():
                return (
                    AnswerabilityStatus.CALCULATION_FAILED,
                    f"Deterministic calculation failed: {reasons[0]}",
                    missing_facts,
                )
            if missing_facts:
                return (
                    AnswerabilityStatus.INSUFFICIENT_EVIDENCE,
                    f"Calculation could not be performed due to missing facts: {', '.join(missing_facts)}",
                    missing_facts,
                )
            return (
                AnswerabilityStatus.CALCULATION_FAILED,
                f"Deterministic calculation failed: {'; '.join(reasons)}",
                missing_facts,
            )

        # 5. Case: Grounding validation failure
        if grounding.status == GroundingStatus.UNGROUNDED:
            return (
                AnswerabilityStatus.GROUNDING_FAILED,
                "Generated claims failed grounding audit against source document evidence.",
                missing_facts,
            )

        # 6. Case: Partial answerability (some required facts missing for multi-part plan)
        if missing_facts and len(plan.required_fact_keys) > len(missing_facts):
            return (
                AnswerabilityStatus.PARTIALLY_ANSWERABLE,
                f"Partially answered inquiry. Missing supporting facts: {', '.join(missing_facts)}",
                missing_facts,
            )

        if missing_facts and len(missing_facts) == len(plan.required_fact_keys):
            return (
                AnswerabilityStatus.INSUFFICIENT_EVIDENCE,
                f"Evidence did not contain the required financial facts: {', '.join(missing_facts)}",
                missing_facts,
            )

        # 7. Fully answerable
        return (
            AnswerabilityStatus.ANSWERABLE,
            "Inquiry successfully answered with fully grounded facts, calculations, and verified citations.",
            [],
        )
