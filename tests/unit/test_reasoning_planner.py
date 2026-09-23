"""Unit tests for deterministic reasoning planner."""

import pytest

from financial_rag.domain.entities.reasoning import ReasoningOperation
from financial_rag.domain.entities.retrieval import (
    FinancialSignals,
    QueryType,
    RetrievalFilter,
    RetrievalQuery,
)
from financial_rag.infrastructure.reasoning.planner import DeterministicReasoningPlanner


@pytest.fixture
def planner() -> DeterministicReasoningPlanner:
    return DeterministicReasoningPlanner()


def test_plan_direct_lookup(planner: DeterministicReasoningPlanner) -> None:
    query = RetrievalQuery(
        raw_query="What was Apple's total revenue in 2024?",
        normalized_query="apple total revenue 2024",
        query_type=QueryType.FACTUAL,
        signals=FinancialSignals(tickers=["AAPL"], metrics=["Revenue"], fiscal_years=[2024]),
        filters=RetrievalFilter(),
    )
    plan = planner.plan(query)
    assert ReasoningOperation.DIRECT_LOOKUP in plan.operations
    assert "Revenue" in plan.target_metrics
    assert "2024" in plan.target_periods


def test_plan_growth_rate(planner: DeterministicReasoningPlanner) -> None:
    query = RetrievalQuery(
        raw_query="What was revenue growth from 2023 to 2024?",
        normalized_query="revenue growth from 2023 to 2024",
        query_type=QueryType.COMPARISON,
        signals=FinancialSignals(
            metrics=["Revenue"], fiscal_years=[2023, 2024], is_comparison=True
        ),
        filters=RetrievalFilter(),
    )
    plan = planner.plan(query)
    assert ReasoningOperation.GROWTH_RATE in plan.operations
    assert len(plan.target_periods) == 2


def test_plan_ratio_calculation(planner: DeterministicReasoningPlanner) -> None:
    query = RetrievalQuery(
        raw_query="What was the ratio of operating income to revenue in 2024?",
        normalized_query="ratio operating income revenue 2024",
        query_type=QueryType.NUMERICAL,
        signals=FinancialSignals(metrics=["Operating Income", "Revenue"], fiscal_years=[2024]),
        filters=RetrievalFilter(),
    )
    plan = planner.plan(query)
    assert ReasoningOperation.RATIO in plan.operations
