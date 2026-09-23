"""Unit tests for high-precision Decimal financial value parser."""

from decimal import Decimal

import pytest

from financial_rag.domain.entities.reasoning import FinancialScale
from financial_rag.infrastructure.reasoning.value_parser import FinancialValueParser


@pytest.fixture
def parser() -> FinancialValueParser:
    return FinancialValueParser()


def test_parse_simple_positive_number(parser: FinancialValueParser) -> None:
    val = parser.parse("$120.50")
    assert val is not None
    assert val.numeric_value == Decimal("120.50")
    assert val.unscaled_value == Decimal("120.50")
    assert val.currency == "USD"
    assert not val.is_negative
    assert not val.is_percentage
    assert val.scale == FinancialScale.EXACT


def test_parse_accounting_parenthetical_negative(parser: FinancialValueParser) -> None:
    val = parser.parse("(1,234.50)")
    assert val is not None
    assert val.numeric_value == Decimal("-1234.50")
    assert val.unscaled_value == Decimal("-1234.50")
    assert val.is_negative
    assert not val.is_percentage


def test_parse_currency_with_parenthetical_negative(parser: FinancialValueParser) -> None:
    val = parser.parse("$(850.00)")
    assert val is not None
    assert val.numeric_value == Decimal("-850.00")
    assert val.is_negative
    assert val.currency == "USD"


def test_parse_billions_scale(parser: FinancialValueParser) -> None:
    val = parser.parse("$391.0 billion")
    assert val is not None
    assert val.unscaled_value == Decimal("391.0")
    assert val.numeric_value == Decimal("391000000000.0")
    assert val.scale == FinancialScale.BILLIONS
    assert val.currency == "USD"
    assert not val.is_negative


def test_parse_millions_suffix(parser: FinancialValueParser) -> None:
    val = parser.parse("150.25M", context_currency="USD")
    assert val is not None
    assert val.unscaled_value == Decimal("150.25")
    assert val.numeric_value == Decimal("150250000.00")
    assert val.scale == FinancialScale.MILLIONS


def test_parse_negative_percentage(parser: FinancialValueParser) -> None:
    val = parser.parse("(2.5%)")
    assert val is not None
    assert val.unscaled_value == Decimal("-2.5")
    assert val.is_negative
    assert val.is_percentage
    assert val.display_value == "-2.5%"


def test_parse_euro_currency(parser: FinancialValueParser) -> None:
    val = parser.parse("€450.00 million")
    assert val is not None
    assert val.currency == "EUR"
    assert val.numeric_value == Decimal("450000000.00")


def test_parse_gbp_currency(parser: FinancialValueParser) -> None:
    val = parser.parse("£12,500.00")
    assert val is not None
    assert val.currency == "GBP"
    assert val.numeric_value == Decimal("12500.00")


def test_parse_jpy_currency(parser: FinancialValueParser) -> None:
    val = parser.parse("¥50,000")
    assert val is not None
    assert val.currency == "JPY"
    assert val.numeric_value == Decimal("50000")


def test_parse_inr_currency(parser: FinancialValueParser) -> None:
    val = parser.parse("₹1,00,000")
    assert val is not None
    assert val.currency == "INR"
    assert val.numeric_value == Decimal("100000")


def test_parse_table_em_dash_and_nulls(parser: FinancialValueParser) -> None:
    val = parser.parse("—", context_currency="USD")
    assert val is not None
    assert val.numeric_value == Decimal("0")
    assert val.display_value == "$0.00"

    val_na = parser.parse("N/A")
    assert val_na is not None
    assert val_na.numeric_value == Decimal("0")


def test_parse_empty_string(parser: FinancialValueParser) -> None:
    assert parser.parse("") is None
    assert parser.parse("   ") is None


def test_context_scale_propagation(parser: FinancialValueParser) -> None:
    val = parser.parse("391,035", context_units="in millions", context_currency="USD")
    assert val is not None
    assert val.unscaled_value == Decimal("391035")
    assert val.scale == FinancialScale.MILLIONS
    assert val.numeric_value == Decimal("391035000000")
