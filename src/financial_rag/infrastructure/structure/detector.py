"""Financial structure and SEC filing section detector."""

import re
from typing import ClassVar

from financial_rag.common.types import BlockType, DocumentType
from financial_rag.domain.entities.models import DocumentPage
from financial_rag.domain.interfaces.normalizer import StructureDetectorProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.structure.detector")


class FinancialStructureDetector(StructureDetectorProtocol):
    """Detects SEC 10-K/10-Q filing items, Parts, and Financial Statement structures."""

    # Regex patterns for SEC 10-K / 10-Q items and parts
    PART_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:PART\s+(?:I|II|III|IV|1|2|3|4))\b", re.IGNORECASE
    )
    ITEM_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"^(?:ITEM\s+(?:1[A-C]?|[2-9]|1[0-5][A-B]?))\s*[\.\:\-\u2013]?\s*(.+)?", re.IGNORECASE
    )

    # Patterns for core financial statements
    STATEMENT_PATTERNS: ClassVar[list[tuple[re.Pattern[str], str]]] = [
        (
            re.compile(r"consolidated\s+balance\s+sheets?", re.IGNORECASE),
            "Consolidated Balance Sheets",
        ),
        (
            re.compile(
                r"consolidated\s+statements?\s+of\s+(?:income|operations|earnings)", re.IGNORECASE
            ),
            "Consolidated Statements of Operations",
        ),
        (
            re.compile(
                r"consolidated\s+statements?\s+of\s+comprehensive\s+(?:income|loss)", re.IGNORECASE
            ),
            "Consolidated Statements of Comprehensive Income",
        ),
        (
            re.compile(r"consolidated\s+statements?\s+of\s+cash\s+flows?", re.IGNORECASE),
            "Consolidated Statements of Cash Flows",
        ),
        (
            re.compile(
                r"consolidated\s+statements?\s+of\s+(?:stockholders|shareholders)['\u2019]?\s+equity",
                re.IGNORECASE,
            ),
            "Consolidated Statements of Shareholders' Equity",
        ),
        (
            re.compile(r"notes\s+to\s+consolidated\s+financial\s+statements", re.IGNORECASE),
            "Notes to Consolidated Financial Statements",
        ),
    ]

    def detect_structure(
        self,
        pages: list[DocumentPage],
        document_type: DocumentType = DocumentType.OTHER,
    ) -> list[DocumentPage]:
        """Detect and tag hierarchical section paths across document pages."""
        current_part = ""
        current_item = ""
        current_section_path = "General"

        for page in pages:
            page_sections = []

            for block in page.blocks:
                first_line = block.content.split("\n")[0].strip()

                # 1. Check for PART declaration
                part_match = self.PART_PATTERN.match(first_line)
                if part_match:
                    current_part = first_line
                    block.block_type = BlockType.HEADING

                # 2. Check for ITEM declaration
                item_match = self.ITEM_PATTERN.match(first_line)
                if item_match:
                    current_item = first_line
                    block.block_type = BlockType.HEADING

                # 3. Check for Financial Statement Titles
                for stmt_regex, stmt_name in self.STATEMENT_PATTERNS:
                    if stmt_regex.search(first_line):
                        current_item = stmt_name
                        block.block_type = BlockType.HEADING
                        break

                # Formulate hierarchical section path
                path_parts = [p for p in [current_part, current_item] if p]
                if path_parts:
                    current_section_path = " > ".join(path_parts)

                block.section_path = current_section_path
                if current_section_path not in page_sections:
                    page_sections.append(current_section_path)

            page.metadata["detected_sections"] = page_sections
            page.metadata["primary_section"] = (
                page_sections[0] if page_sections else current_section_path
            )

        logger.info(f"Structure detection completed across {len(pages)} pages")
        return pages
