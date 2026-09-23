"""Unit tests for fiscal reporting period normalizer."""

import pytest

from financial_rag.infrastructure.reasoning.period_normalizer import FiscalPeriodNormalizer


@pytest.fixture
def normalizer() -> FiscalPeriodNormalizer:
    return FiscalPeriodNormalizer()


def test_normalize_fy_explicit(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("FY2024")
    assert p.fiscal_year == 2024
    assert p.period_type == "FY"
    assert p.label == "FY2024"
    assert not p.is_uncertain


def test_normalize_plain_year(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("2023")
    assert p.fiscal_year == 2023
    assert p.period_type == "FY"
    assert p.label == "FY2023"


def test_normalize_quarter(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("Q3 2024")
    assert p.fiscal_year == 2024
    assert p.period_type == "Q3"
    assert p.label == "Q3 2024"


def test_normalize_written_quarter(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("First Quarter 2024")
    assert p.fiscal_year == 2024
    assert p.period_type == "Q1"
    assert p.label == "Q1 2024"


def test_normalize_three_months_ended(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("Three Months Ended September 30, 2024")
    assert p.fiscal_year == 2024
    assert p.period_type == "Q3"
    assert p.label == "Q3 2024"


def test_normalize_ttm(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("Trailing Twelve Months 2024")
    assert p.fiscal_year == 2024
    assert p.period_type == "TTM"
    assert p.label == "TTM 2024"


def test_normalize_empty_with_default(normalizer: FiscalPeriodNormalizer) -> None:
    p = normalizer.normalize("", default_year=2024)
    assert p.fiscal_year == 2024
    assert p.period_type == "FY"
    assert not p.is_uncertain
