"""Unit tests for deterministic fact extractor layer."""

from decimal import Decimal

import pytest

from financial_rag.domain.entities.reasoning import FinancialScale
from financial_rag.infrastructure.reasoning.fact_extractor import DeterministicFactExtractor
from tests.fixtures.financial_reasoning_fixtures import (
    make_sample_apple_narrative_evidence,
    make_sample_apple_table_evidence,
)


@pytest.fixture
def extractor() -> DeterministicFactExtractor:
    return DeterministicFactExtractor()


def test_extract_facts_from_table(extractor: DeterministicFactExtractor) -> None:
    table_evidence = make_sample_apple_table_evidence()
    facts = extractor.extract_facts([table_evidence])

    assert len(facts) >= 6
    # Find Revenue 2024 fact
    rev_2024 = next(
        (f for f in facts if "sales" in f.metric.lower() and f.period.fiscal_year == 2024),
        None,
    )
    assert rev_2024 is not None
    assert rev_2024.value.unscaled_value == Decimal("391035")
    assert rev_2024.value.scale == FinancialScale.MILLIONS
    assert rev_2024.value.numeric_value == Decimal("391035000000")
    assert rev_2024.extraction_method == "table_structured"
    assert rev_2024.document_id == "doc-aapl-10k-2024"
    assert rev_2024.page_number == 45
    assert rev_2024.table_id == "tbl-ops-2024"


def test_extract_accounting_negative_from_table(extractor: DeterministicFactExtractor) -> None:
    table_evidence = make_sample_apple_table_evidence()
    facts = extractor.extract_facts([table_evidence])

    # Cost of sales 2024 is (210,352)
    cogs_2024 = next(
        (f for f in facts if "cost of sales" in f.metric.lower() and f.period.fiscal_year == 2024),
        None,
    )
    assert cogs_2024 is not None
    assert cogs_2024.value.is_negative
    assert cogs_2024.value.numeric_value == Decimal("-210352000000")


def test_extract_facts_from_narrative(extractor: DeterministicFactExtractor) -> None:
    narrative_evidence = make_sample_apple_narrative_evidence()
    facts = extractor.extract_facts([narrative_evidence])

    assert len(facts) >= 1
    # Check Net sales 2024 from narrative
    sales_fact = next(
        (f for f in facts if "sales" in f.metric.lower() or "revenue" in f.metric.lower()),
        None,
    )
    assert sales_fact is not None
    assert sales_fact.value.numeric_value == Decimal("391000000000.0")
    assert sales_fact.extraction_method == "narrative_regex"
    assert sales_fact.page_number == 30
    assert sales_fact.source_evidence_id == str(narrative_evidence.chunk_id)
