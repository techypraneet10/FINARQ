"""Financial table extraction from page text and structural layout blocks."""

import re
from uuid import uuid4

from financial_rag.common.types import BlockType, TableId
from financial_rag.domain.entities.models import DocumentPage, FinancialTable
from financial_rag.domain.interfaces.table import TableExtractorProtocol
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer

logger = get_logger("financial_rag.infrastructure.table.extractor")


class FinancialTableExtractor(TableExtractorProtocol):
    """Extracts and enhances financial tables from DocumentPage entities."""

    def __init__(self, normalizer: FinancialTableNormalizer | None = None) -> None:
        self._normalizer = normalizer or FinancialTableNormalizer()

    def extract_tables(self, page: DocumentPage) -> list[FinancialTable]:
        """Extract and normalize all tables present on a document page."""
        tables: list[FinancialTable] = []

        # 1. First process any native tables already identified by PDF parser
        for tab in page.tables:
            norm_tab = self._normalizer.normalize_table(tab)
            tables.append(norm_tab)

        # 2. If no native tables found, check layout blocks for tabular text patterns
        if not tables:
            heuristic_tables = self._extract_tables_from_blocks(page)
            tables.extend(heuristic_tables)

        return tables

    def _extract_tables_from_blocks(self, page: DocumentPage) -> list[FinancialTable]:
        """Detect multi-column tabular patterns in text blocks (e.g. balance sheet rows)."""
        tables: list[FinancialTable] = []

        for block in page.blocks:
            if (
                block.block_type == BlockType.TABLE
                or "\t" in block.content
                or "   " in block.content
            ):
                lines = [line.strip() for line in block.content.split("\n") if line.strip()]
                if len(lines) < 2:
                    continue

                # Check if lines have multiple numeric tokens
                table_lines: list[list[str]] = []
                for line in lines:
                    # Split by multiple spaces or tabs
                    parts = [p.strip() for p in re.split(r"\s{2,}|\t", line) if p.strip()]
                    if len(parts) >= 2:
                        table_lines.append(parts)

                if len(table_lines) >= 2:
                    headers = table_lines[0]
                    rows = table_lines[1:]
                    table_id: TableId = str(uuid4())
                    raw_tab = FinancialTable(
                        id=table_id,
                        page_number=page.page_number,
                        title=f"Extracted Table (Page {page.page_number})",
                        headers=headers,
                        rows=rows,
                        bounding_box=block.bounding_box,
                    )
                    norm_tab = self._normalizer.normalize_table(raw_tab)
                    tables.append(norm_tab)

        return tables
