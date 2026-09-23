"""Deterministic query reasoning planner formulating structured execution plans."""

import re
from uuid import uuid4

from financial_rag.domain.entities.reasoning import ReasoningOperation, ReasoningPlan
from financial_rag.domain.entities.retrieval import RetrievalQuery
from financial_rag.domain.interfaces.reasoning import ReasoningPlannerProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.planner")


class DeterministicReasoningPlanner(ReasoningPlannerProtocol):
    """Inspects query text and structural signals to construct an explicit ReasoningPlan."""

    def plan(self, query: RetrievalQuery) -> ReasoningPlan:
        """Construct deterministic execution plan based on financial intent."""
        plan_id = str(uuid4())
        raw_text = query.raw_query.lower()
        signals = query.signals

        target_metrics = list(signals.metrics) if signals.metrics else []
        target_periods = [str(y) for y in signals.fiscal_years] + list(signals.fiscal_periods)
        target_companies = list(signals.tickers) + list(signals.company_names)

        # Infer metrics from query text if not extracted by signals
        if not target_metrics:
            for kw in (
                "revenue",
                "net income",
                "operating income",
                "gross profit",
                "total assets",
                "cash",
                "debt",
            ):
                if kw in raw_text:
                    target_metrics.append(kw.title())

        # Infer periods if not in signals
        if not target_periods:
            yr_matches = re.findall(r"(20\d{2}|19\d{2})", raw_text)
            if yr_matches:
                target_periods.extend(yr_matches)

        operations: list[ReasoningOperation] = []
        steps_desc: list[str] = []

        is_growth = "growth" in raw_text or "growth rate" in raw_text
        is_pct_change = (
            "% change" in raw_text
            or "percentage change" in raw_text
            or "percent change" in raw_text
        )
        is_difference = (
            "difference" in raw_text
            or "change" in raw_text
            or "increase" in raw_text
            or "decrease" in raw_text
            or "delta" in raw_text
        )
        is_ratio = (
            "ratio" in raw_text
            or "margin" in raw_text
            or "as a percentage of" in raw_text
            or "divided by" in raw_text
        )
        is_sum = (
            "sum" in raw_text
            or "total" in raw_text
            or "combined" in raw_text
            or "aggregate" in raw_text
        )
        is_avg = "average" in raw_text or "mean" in raw_text
        is_trend = "trend" in raw_text or "historically" in raw_text or "over time" in raw_text

        if is_growth:
            operations.append(ReasoningOperation.GROWTH_RATE)
            steps_desc.append(
                "Calculate percentage growth rate between base and target reporting periods."
            )
        elif is_pct_change:
            operations.append(ReasoningOperation.PERCENTAGE_CHANGE)
            steps_desc.append("Calculate percentage change ((new - old) / |old|) * 100.")
        elif is_difference:
            operations.append(ReasoningOperation.DIFFERENCE)
            steps_desc.append("Calculate numerical difference between periods or metrics.")
        elif is_ratio:
            operations.append(ReasoningOperation.RATIO)
            steps_desc.append(
                "Calculate financial ratio between numerator and denominator metrics."
            )
        elif is_sum and len(target_periods) > 1:
            operations.append(ReasoningOperation.SUM)
            steps_desc.append("Aggregate sum across reporting periods.")
        elif is_avg:
            operations.append(ReasoningOperation.AVERAGE)
            steps_desc.append("Calculate arithmetic mean across periods.")
        elif is_trend or (len(target_periods) > 2):
            operations.append(ReasoningOperation.TREND)
            steps_desc.append("Analyze multi-period chronological trend.")
        elif signals.is_comparison or len(target_periods) > 1:
            operations.append(ReasoningOperation.DIFFERENCE)
            operations.append(ReasoningOperation.PERCENTAGE_CHANGE)
            steps_desc.append(
                "Compare multi-period values and compute delta and percentage change."
            )
        else:
            operations.append(ReasoningOperation.DIRECT_LOOKUP)
            steps_desc.append("Direct lookup of targeted financial metric and period.")

        # Derive required fact keys for sufficiency evaluation
        required_fact_keys = []
        if target_metrics and target_periods:
            for m in target_metrics:
                for p in target_periods:
                    required_fact_keys.append(f"{m.lower()}_{p.lower()}")
        elif target_metrics:
            for m in target_metrics:
                required_fact_keys.append(m.lower())

        plan = ReasoningPlan(
            plan_id=plan_id,
            query=query.raw_query,
            operations=operations,
            target_metrics=target_metrics,
            target_periods=target_periods,
            target_companies=target_companies,
            required_fact_keys=required_fact_keys,
            steps_description=steps_desc,
            is_multi_period=len(target_periods) > 1 or signals.is_multi_period,
            is_comparison=signals.is_comparison or len(operations) > 1,
        )

        logger.info(
            f"Formulated reasoning plan '{plan_id}' with operations: {[op.value for op in operations]}"
        )
        return plan
