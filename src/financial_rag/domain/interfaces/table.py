"""Architectural contract for financial table extraction and normalization."""

from typing import Protocol, runtime_checkable

from financial_rag.domain.entities.models import DocumentPage, FinancialTable


@runtime_checkable
class TableExtractorProtocol(Protocol):
    """Contract for extracting tabular structures from parsed pages."""

    def extract_tables(self, page: DocumentPage) -> list[FinancialTable]:
        """Identify and extract financial tables from page layout."""
        ...


@runtime_checkable
class TableNormalizerProtocol(Protocol):
    """Contract for standardizing headers, financial scales, currencies, and negative parentheticals."""

    def normalize_table(self, table: FinancialTable) -> FinancialTable:
        """Normalize table values, units, parenthetical negatives, and markdown rendering."""
        ...
