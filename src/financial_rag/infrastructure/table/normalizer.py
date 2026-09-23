"""Financial table normalizer standardizing negative parentheticals, units, and markdown rendering."""

import re
from typing import ClassVar

from financial_rag.domain.entities.models import FinancialTable
from financial_rag.domain.entities.value_objects import TableCell
from financial_rag.domain.interfaces.table import TableNormalizerProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.table.normalizer")


class FinancialTableNormalizer(TableNormalizerProtocol):
    """Normalizes financial numbers, negative parentheses, scale multipliers, and markdown tables."""

    # Regex for financial numbers in parenthetical negative notation: (1,234.56) or $(1,234) or (2.1%)
    PARENTHETICAL_NEGATIVE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^\s*[\$\€\£\¥]?\s*\(\s*([\d,]+(?:\.\d+)?)\s*\%?\s*\)\s*\%?\s*$"
    )
    # Regex for standard positive numbers
    NUMERIC_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^\s*[\$\€\£\¥]?\s*([\+\-]?[\d,]+(?:\.\d+)?)\s*\%?\s*$"
    )

    def parse_financial_number(self, raw_str: str) -> float | None:
        """Parse financial string with currency, commas, and parenthetical negatives into float."""
        if not raw_str or not raw_str.strip():
            return None

        clean = raw_str.strip().replace("—", "").replace("-", "")
        if not clean:
            return 0.0

        # Check parenthetical negative e.g. (1,234.50)
        match_neg = self.PARENTHETICAL_NEGATIVE_PATTERN.match(raw_str)
        if match_neg:
            num_str = match_neg.group(1).replace(",", "")
            try:
                return -float(num_str)
            except ValueError:
                return None

        # Check regular number
        match_pos = self.NUMERIC_PATTERN.match(raw_str)
        if match_pos:
            num_str = match_pos.group(1).replace(",", "")
            try:
                return float(num_str)
            except ValueError:
                return None

        return None

    def detect_units_and_scale(self, text: str) -> tuple[str, str, float]:
        """Detect currency, unit descriptor, and multiplier scale from header/title text."""
        lower = text.lower()
        currency = "USD"
        if "€" in text or "eur" in lower:
            currency = "EUR"
        elif "£" in text or "gbp" in lower:
            currency = "GBP"
        elif "¥" in text or "jpy" in lower:
            currency = "JPY"
        elif "$" in text or "usd" in lower or "dollar" in lower:
            currency = "USD"

        units = ""
        scale = 1.0

        if "in millions" in lower or "in millions," in lower or "(millions)" in lower:
            units = "in millions"
            scale = 1_000_000.0
        elif "in thousands" in lower or "in thousands," in lower or "(thousands)" in lower:
            units = "in thousands"
            scale = 1_000.0
        elif "in billions" in lower or "in billions," in lower or "(billions)" in lower:
            units = "in billions"
            scale = 1_000_000_000.0

        return currency, units, scale

    def generate_markdown(self, headers: list[str], rows: list[list[str]], title: str = "") -> str:
        """Render table as a standard Markdown table string."""
        if not headers and not rows:
            return ""

        col_count = len(headers) if headers else (len(rows[0]) if rows else 0)
        if col_count == 0:
            return ""

        # Normalize column counts across rows
        norm_headers = (
            [h or f"Col {i + 1}" for i, h in enumerate(headers)]
            if headers
            else [f"Col {i + 1}" for i in range(col_count)]
        )
        if len(norm_headers) < col_count:
            norm_headers.extend([f"Col {i + 1}" for i in range(len(norm_headers), col_count)])

        md_lines = []
        if title:
            md_lines.append(f"### {title}\n")

        # Header line
        header_line = "| " + " | ".join(norm_headers) + " |"
        separator_line = "| " + " | ".join(["---"] * len(norm_headers)) + " |"
        md_lines.append(header_line)
        md_lines.append(separator_line)

        # Rows
        for row in rows:
            pad_row = [str(c).replace("\n", " ").replace("|", "\\|").strip() for c in row]
            if len(pad_row) < len(norm_headers):
                pad_row.extend([""] * (len(norm_headers) - len(pad_row)))
            elif len(pad_row) > len(norm_headers):
                pad_row = pad_row[: len(norm_headers)]
            md_lines.append("| " + " | ".join(pad_row) + " |")

        return "\n".join(md_lines)

    def normalize_table(self, table: FinancialTable) -> FinancialTable:
        """Normalize table values, units, and markdown representations."""
        # Detect currency and unit scales from title or metadata
        title_context = f"{table.title} {' '.join(table.headers)}"
        currency, units, scale = self.detect_units_and_scale(title_context)

        if not table.currency or table.currency == "USD":
            table.currency = currency
        if not table.units:
            table.units = units
            table.scale = scale

        # Normalize cells
        normalized_cells: list[TableCell] = []
        normalized_rows: list[list[str]] = []

        for r_idx, row in enumerate(table.rows):
            norm_row = []
            for c_idx, cell_val in enumerate(row):
                cell_str = str(cell_val).strip()
                numeric = self.parse_financial_number(cell_str)

                # Format negative numbers cleanly in text representation
                formatted_text = cell_str
                if numeric is not None and numeric < 0 and "(" in cell_str:
                    formatted_text = (
                        f"-{abs(numeric):,g}" if "." not in cell_str else f"-{abs(numeric):,.2f}"
                    )

                norm_row.append(formatted_text)
                normalized_cells.append(
                    TableCell(
                        row_index=r_idx,
                        col_index=c_idx,
                        text=formatted_text,
                        numeric_value=numeric,
                        is_header=False,
                        raw_text=cell_str,
                    )
                )
            normalized_rows.append(norm_row)

        table.rows = normalized_rows
        table.cells = normalized_cells

        # Generate markdown representation
        table.markdown_repr = self.generate_markdown(
            headers=table.headers,
            rows=normalized_rows,
            title=table.title,
        )

        return table
