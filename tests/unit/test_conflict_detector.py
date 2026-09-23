"""Unit tests for conflict detection engine."""

from decimal import Decimal

import pytest

from financial_rag.infrastructure.reasoning.conflict_detector import DeterministicConflictDetector
from financial_rag.infrastructure.reasoning.fact_extractor import DeterministicFactExtractor
from tests.fixtures.financial_reasoning_fixtures import (
    make_sample_apple_table_evidence,
    make_sample_conflicting_narrative_evidence,
)


@pytest.fixture
def conflict_detector() -> DeterministicConflictDetector:
    return DeterministicConflictDetector()


def test_detect_table_vs_narrative_conflict(
    conflict_detector: DeterministicConflictDetector,
) -> None:
    extractor = DeterministicFactExtractor()
    table_ev = make_sample_apple_table_evidence()
    conflict_narrative_ev = make_sample_conflicting_narrative_evidence()

    facts = extractor.extract_facts([table_ev, conflict_narrative_ev])
    conflicts = conflict_detector.detect_conflicts(facts)

    assert len(conflicts) >= 1
    net_income_conflict = next(
        (c for c in conflicts if "net income" in c.metric.lower() or "income" in c.metric.lower()),
        None,
    )
    assert net_income_conflict is not None
    assert len(net_income_conflict.conflicting_facts) == 2
    assert "Discrepancy detected" in net_income_conflict.difference_description
    assert net_income_conflict.resolved
    assert "table-first" in str(net_income_conflict.resolution_rationale)


def test_no_conflict_when_values_agree(
    conflict_detector: DeterministicConflictDetector,
) -> None:
    from tests.unit.test_financial_calculator import make_fact

    f1 = make_fact("Revenue", "$100.00", Decimal("100.00"), 2024)
    f2 = make_fact("Revenue", "$100.05", Decimal("100.05"), 2024)  # 0.05% diff < 0.1% tolerance

    conflicts = conflict_detector.detect_conflicts([f1, f2])
    assert len(conflicts) == 0
