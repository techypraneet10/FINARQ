"""Unit tests for deterministic financial calculator using Decimal arithmetic."""

from decimal import Decimal

import pytest

from financial_rag.domain.entities.reasoning import (
    FinancialFact,
    FinancialScale,
    FinancialValue,
    FiscalPeriod,
    ReasoningOperation,
)
from financial_rag.infrastructure.reasoning.calculator import (
    DeterministicFinancialCalculator,
)


def make_fact(
    metric: str,
    raw_str: str,
    numeric_val: Decimal,
    period_year: int,
    period_type: str = "FY",
    currency: str | None = "USD",
    company: str = "Apple Inc.",
    ticker: str = "AAPL",
    is_percentage: bool = False,
) -> FinancialFact:
    val = FinancialValue(
        raw_value=raw_str,
        display_value=raw_str,
        numeric_value=numeric_val,
        unscaled_value=numeric_val,
        currency=currency if not is_percentage else None,
        scale=FinancialScale.EXACT,
        unit=currency or "%",
        is_negative=numeric_val < 0,
        is_percentage=is_percentage,
    )
    period = FiscalPeriod(
        fiscal_year=period_year,
        period_type=period_type,
        source_text=f"{period_type} {period_year}",
    )
    return FinancialFact(
        fact_id=f"fact-{metric}-{period_year}",
        metric=metric,
        value=val,
        period=period,
        company=company,
        ticker=ticker,
        document_id="doc-1",
        document_version_id="ver-1",
        page_number=10,
        chunk_id="chunk-1",
        table_id=None,
        source_evidence_id="chunk-1",
        extraction_method="table_structured",
        confidence=1.0,
        source_text=f"{metric}: {raw_str}",
    )


@pytest.fixture
def calculator() -> DeterministicFinancialCalculator:
    return DeterministicFinancialCalculator()


def test_direct_lookup(calculator: DeterministicFinancialCalculator) -> None:
    fact = make_fact("Revenue", "$391.035B", Decimal("391035000000"), 2024)
    res = calculator.execute(ReasoningOperation.DIRECT_LOOKUP, [fact])
    assert res.success
    assert res.raw_result == Decimal("391035000000")
    assert res.display_result == "$391.035B"


def test_difference_calculation(calculator: DeterministicFinancialCalculator) -> None:
    fact_2024 = make_fact("Revenue", "$391.035B", Decimal("391035000000"), 2024)
    fact_2023 = make_fact("Revenue", "$383.285B", Decimal("383285000000"), 2023)
    res = calculator.execute(ReasoningOperation.DIFFERENCE, [fact_2024, fact_2023])
    assert res.success
    assert res.raw_result == Decimal("7750000000")  # 391.035 - 383.285 = 7.75B
    assert "$7.75 billion" in res.display_result


def test_percentage_change_and_growth_rate(calculator: DeterministicFinancialCalculator) -> None:
    fact_2023 = make_fact("Revenue", "$100.00", Decimal("100.00"), 2023)
    fact_2024 = make_fact("Revenue", "$120.00", Decimal("120.00"), 2024)
    res = calculator.execute(ReasoningOperation.PERCENTAGE_CHANGE, [fact_2023, fact_2024])
    assert res.success
    assert res.rounded_result == Decimal("20.00")
    assert res.display_result == "+20.00%"

    # Test growth rate
    res_growth = calculator.execute(ReasoningOperation.GROWTH_RATE, [fact_2023, fact_2024])
    assert res_growth.success
    assert res_growth.rounded_result == Decimal("20.00")


def test_negative_percentage_change(calculator: DeterministicFinancialCalculator) -> None:
    fact_2022 = make_fact("Revenue", "$394.328B", Decimal("394328000000"), 2022)
    fact_2023 = make_fact("Revenue", "$383.285B", Decimal("383285000000"), 2023)
    res = calculator.execute(ReasoningOperation.PERCENTAGE_CHANGE, [fact_2022, fact_2023])
    assert res.success
    assert res.rounded_result < 0
    assert "-" in res.display_result


def test_division_by_zero_protection(calculator: DeterministicFinancialCalculator) -> None:
    fact_zero = make_fact("Revenue", "$0.00", Decimal("0.00"), 2023)
    fact_new = make_fact("Revenue", "$100.00", Decimal("100.00"), 2024)
    res = calculator.execute(ReasoningOperation.PERCENTAGE_CHANGE, [fact_zero, fact_new])
    assert not res.success
    assert "division by zero" in str(res.error_message).lower()
    assert res.raw_result == Decimal("0")


def test_ratio_calculation(calculator: DeterministicFinancialCalculator) -> None:
    fact_op_income = make_fact("Operating Income", "$123.217B", Decimal("123217000000"), 2024)
    fact_revenue = make_fact("Revenue", "$391.035B", Decimal("391035000000"), 2024)
    res = calculator.execute(ReasoningOperation.RATIO, [fact_op_income, fact_revenue])
    assert res.success
    # 123217 / 391035 ~= 0.3151
    assert res.rounded_result == Decimal("0.3151")


def test_ratio_division_by_zero(calculator: DeterministicFinancialCalculator) -> None:
    num = make_fact("Net Income", "$50.00", Decimal("50.00"), 2024)
    den = make_fact("Revenue", "$0.00", Decimal("0.00"), 2024)
    res = calculator.execute(ReasoningOperation.RATIO, [num, den])
    assert not res.success
    assert "division by zero" in str(res.error_message).lower()


def test_sum_and_average(calculator: DeterministicFinancialCalculator) -> None:
    f1 = make_fact("Revenue", "$100", Decimal("100"), 2022)
    f2 = make_fact("Revenue", "$200", Decimal("200"), 2023)
    f3 = make_fact("Revenue", "$300", Decimal("300"), 2024)

    sum_res = calculator.execute(ReasoningOperation.SUM, [f1, f2, f3])
    assert sum_res.success
    assert sum_res.raw_result == Decimal("600")

    avg_res = calculator.execute(ReasoningOperation.AVERAGE, [f1, f2, f3])
    assert avg_res.success
    assert avg_res.raw_result == Decimal("200")


def test_min_and_max(calculator: DeterministicFinancialCalculator) -> None:
    f1 = make_fact("Revenue", "$150", Decimal("150"), 2022)
    f2 = make_fact("Revenue", "$100", Decimal("100"), 2023)
    f3 = make_fact("Revenue", "$250", Decimal("250"), 2024)

    min_res = calculator.execute(ReasoningOperation.MIN, [f1, f2, f3])
    assert min_res.success
    assert min_res.raw_result == Decimal("100")

    max_res = calculator.execute(ReasoningOperation.MAX, [f1, f2, f3])
    assert max_res.success
    assert max_res.raw_result == Decimal("250")


def test_trend_analysis(calculator: DeterministicFinancialCalculator) -> None:
    f1 = make_fact("Revenue", "$100M", Decimal("100000000"), 2022)
    f2 = make_fact("Revenue", "$120M", Decimal("120000000"), 2023)
    f3 = make_fact("Revenue", "$150M", Decimal("150000000"), 2024)

    trend_res = calculator.execute(ReasoningOperation.TREND, [f1, f2, f3])
    assert trend_res.success
    assert "increased" in trend_res.display_result
    assert trend_res.raw_result == Decimal("50000000")


def test_incompatible_currencies_rejected(calculator: DeterministicFinancialCalculator) -> None:
    f_usd = make_fact("Revenue", "$100", Decimal("100"), 2024, currency="USD")
    f_eur = make_fact("Revenue", "€100", Decimal("100"), 2024, currency="EUR")
    res = calculator.execute(ReasoningOperation.DIFFERENCE, [f_usd, f_eur])
    assert not res.success
    assert (
        "incompatible" in str(res.error_message).lower()
        or "currencies" in str(res.error_message).lower()
    )


def test_incompatible_units_percentage_and_currency(
    calculator: DeterministicFinancialCalculator,
) -> None:
    f_curr = make_fact("Revenue", "$100", Decimal("100"), 2024, currency="USD", is_percentage=False)
    f_pct = make_fact("Margin", "20%", Decimal("20"), 2024, currency=None, is_percentage=True)
    res = calculator.execute(ReasoningOperation.SUM, [f_curr, f_pct])
    assert not res.success
    assert (
        "incompatible" in str(res.error_message).lower()
        or "units" in str(res.error_message).lower()
    )


def test_incompatible_companies_rejected_without_override(
    calculator: DeterministicFinancialCalculator,
) -> None:
    f_aapl = make_fact("Revenue", "$100", Decimal("100"), 2024, company="Apple Inc.", ticker="AAPL")
    f_msft = make_fact(
        "Revenue", "$100", Decimal("100"), 2024, company="Microsoft Corp.", ticker="MSFT"
    )
    res = calculator.execute(ReasoningOperation.DIFFERENCE, [f_aapl, f_msft])
    assert not res.success
    assert (
        "incompatible" in str(res.error_message).lower()
        or "company" in str(res.error_message).lower()
    )
