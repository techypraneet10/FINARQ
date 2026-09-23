"""Unit tests for FinancialTableNormalizer and table extraction."""

import pytest

from financial_rag.domain.entities.models import FinancialTable
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer


@pytest.mark.unit
def test_table_normalizer_financial_parentheses() -> None:
    normalizer = FinancialTableNormalizer()

    table = FinancialTable(
        id="tbl-1",
        page_number=2,
        title="CONSOLIDATED BALANCE SHEETS (In millions)",
        headers=["Item", "2023", "2022"],
        rows=[
            ["Cash and cash equivalents", "$ 28,150", "$ 24,680"],
            ["Unrealized investment loss", "(1,234.50)", "(850.00)"],
            ["Total Assets", "$ 58,455.50", "$ 49,940.00"],
        ],
    )

    normalized = normalizer.normalize_table(table)

    # Verify currency and scale detection
    assert normalized.currency in ["$", "USD"]
    assert normalized.scale == 1_000_000.0
    assert "millions" in normalized.units

    # Verify parenthetical negative conversion in numeric values
    cell_map = {(c.row_index, c.col_index): c.numeric_value for c in normalized.cells}
    assert cell_map.get((1, 1)) == -1234.5
    assert cell_map.get((1, 2)) == -850.0
    assert cell_map.get((0, 1)) == 28150.0

    # Verify markdown table generation
    assert "| Item | 2023 | 2022 |" in normalized.markdown_repr
    assert "| Cash and cash equivalents | $ 28,150 | $ 24,680 |" in normalized.markdown_repr


@pytest.mark.unit
def test_table_normalizer_empty_and_footnote() -> None:
    normalizer = FinancialTableNormalizer()

    table = FinancialTable(
        id="tbl-2",
        page_number=5,
        title="Revenue by Segment",
        headers=["Segment", "Growth %"],
        rows=[
            ["Services", "16.5%"],
            ["Hardware", "(2.1%)"],
        ],
        footnotes=["[1] Excludes foreign currency fluctuations"],
    )

    normalized = normalizer.normalize_table(table)
    assert len(normalized.footnotes) == 1
    assert "[1]" in normalized.footnotes[0]
    cell_map = {(c.row_index, c.col_index): c.numeric_value for c in normalized.cells}
    assert cell_map.get((1, 1)) == -2.1
