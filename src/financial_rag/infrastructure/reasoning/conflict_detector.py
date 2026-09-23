"""Conflict detection engine discovering factual and numerical discrepancies across evidence."""

from collections import defaultdict
from decimal import Decimal
from uuid import uuid4

from financial_rag.domain.entities.reasoning import EvidenceConflict, FinancialFact
from financial_rag.domain.interfaces.reasoning import ConflictDetectorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.reasoning.conflict_detector")


class DeterministicConflictDetector(ConflictDetectorProtocol):
    """Detects discrepancies between multiple facts for the same company, metric, and period."""

    def __init__(self, tolerance_pct: Decimal = Decimal("0.001")) -> None:
        """tolerance_pct: Relative difference threshold (default 0.1% = 0.001) above which values are in conflict."""
        self.tolerance_pct = tolerance_pct

    def _normalize_metric_key(self, metric: str) -> str:
        """Normalize metric name for fuzzy grouping."""
        clean = (
            metric.lower()
            .replace("total", "")
            .replace("net", "")
            .replace("consolidated", "")
            .strip()
        )
        return clean

    def detect_conflicts(
        self,
        facts: list[FinancialFact],
    ) -> list[EvidenceConflict]:
        """Detect and structure discrepancies among extracted facts."""
        conflicts: list[EvidenceConflict] = []
        if len(facts) <= 1:
            return conflicts

        # Group facts by (company, normalized_metric, period_label)
        groups: dict[tuple[str, str, str], list[FinancialFact]] = defaultdict(list)
        for fact in facts:
            company_key = (fact.company or fact.ticker or "Unknown").strip().upper()
            metric_key = self._normalize_metric_key(fact.metric)
            period_key = fact.period.label
            groups[(company_key, metric_key, period_key)].append(fact)

        for (_comp, _metric_norm, period_label), group_facts in groups.items():
            if len(group_facts) <= 1:
                continue

            # Compare values pairwise
            distinct_values: list[FinancialFact] = []
            for f in group_facts:
                val = f.value.numeric_value
                # Check if this value is close to any already collected distinct value
                is_duplicate = False
                for seen_fact in distinct_values:
                    seen_val = seen_fact.value.numeric_value
                    diff = abs(val - seen_val)
                    denom = max(abs(val), abs(seen_val))
                    if denom == Decimal("0") or (diff / denom) <= self.tolerance_pct:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    distinct_values.append(f)

            if len(distinct_values) > 1:
                conflict_id = str(uuid4())
                metric_name = distinct_values[0].metric
                val_descriptions = [
                    f"{f.value.display_value} (from {f.extraction_method}, Page {f.page_number})"
                    for f in distinct_values
                ]
                diff_desc = (
                    f"Discrepancy detected for '{metric_name}' in {period_label}: "
                    + " vs ".join(val_descriptions)
                )

                # Apply deterministic preference hierarchy:
                # 1. table_structured / table_cell
                # 2. narrative_regex
                resolved_fact = None
                table_facts = [f for f in distinct_values if "table" in f.extraction_method]
                if table_facts:
                    resolved_fact = max(table_facts, key=lambda f: f.confidence)
                    resolution_rationale = (
                        f"Resolved via table-first hierarchy: selected authoritative table fact "
                        f"({resolved_fact.value.display_value}, Page {resolved_fact.page_number}) "
                        f"over narrative mention."
                    )
                else:
                    resolved_fact = max(distinct_values, key=lambda f: f.confidence)
                    resolution_rationale = f"Resolved via confidence scoring: selected fact with confidence {resolved_fact.confidence}."

                logger.warning(f"Conflict identified: {diff_desc}")
                conflicts.append(
                    EvidenceConflict(
                        conflict_id=conflict_id,
                        metric=metric_name,
                        period=period_label,
                        conflicting_facts=distinct_values,
                        difference_description=diff_desc,
                        resolved=True,
                        resolved_fact_id=resolved_fact.fact_id if resolved_fact else None,
                        resolution_rationale=resolution_rationale,
                    )
                )

        return conflicts
