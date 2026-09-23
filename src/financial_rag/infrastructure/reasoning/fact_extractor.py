"""Deterministic fact extraction layer parsing structured facts from financial tables and narratives."""

import re
from typing import ClassVar
from uuid import uuid4

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.reasoning import FinancialFact
from financial_rag.domain.entities.retrieval import RankedEvidence
from financial_rag.domain.interfaces.reasoning import (
    FactExtractorProtocol,
    FinancialValueParserProtocol,
    PeriodNormalizerProtocol,
)
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.reasoning.period_normalizer import FiscalPeriodNormalizer
from financial_rag.infrastructure.reasoning.value_parser import FinancialValueParser

logger = get_logger("financial_rag.infrastructure.reasoning.fact_extractor")


class DeterministicFactExtractor(FactExtractorProtocol):
    """Extracts verified FinancialFact instances from retrieved table and text evidence."""

    # Standard financial metrics keywords
    METRIC_KEYWORDS: ClassVar[list[str]] = [
        "revenue",
        "total revenue",
        "total net sales",
        "net sales",
        "sales",
        "cost of sales",
        "cost of revenue",
        "cost of goods sold",
        "gross profit",
        "gross margin",
        "operating income",
        "operating profit",
        "operating expenses",
        "research and development",
        "selling, general and administrative",
        "net income",
        "net earnings",
        "earnings before taxes",
        "provision for income taxes",
        "total assets",
        "total current assets",
        "cash and cash equivalents",
        "marketable securities",
        "inventories",
        "total liabilities",
        "total current liabilities",
        "long-term debt",
        "total stockholders equity",
        "shareholders equity",
        "operating cash flow",
        "free cash flow",
        "capital expenditures",
        "earnings per share",
        "diluted earnings per share",
        "basic earnings per share",
    ]

    # Narrative extraction patterns
    NARRATIVE_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        # "Total net sales were $391.0 billion in 2024"
        re.compile(
            r"([A-Za-z\s,\-'\&]+?)\s+(?:was|were|reached|totaled|amounted to|of|is)\s+([\$€£¥₹]?\s*[\(\+\-]?[\d,]+(?:\.\d+)?\s*[\$€£¥₹]?\s*(?:[KkMmBbTt%]|thousand|million|billion|trillion|percent)?)\s*(?:for|in|during)?\s*(?:the\s+)?(fiscal\s+(?:year\s+)?20\d{2}|FY\s*20\d{2}|20\d{2}|Q[1-4]\s*20\d{2}|First Quarter 20\d{2})?",
            re.IGNORECASE,
        ),
        # "In 2024, revenue was $391.0 billion"
        re.compile(
            r"(?:in|for|during)\s+(?:the\s+)?(fiscal\s+(?:year\s+)?20\d{2}|FY\s*20\d{2}|20\d{2}|Q[1-4]\s*20\d{2}),?\s+([A-Za-z\s,\-'\&]+?)\s+(?:was|were|reached|totaled)\s+([\$€£¥₹]?\s*[\(\+\-]?[\d,]+(?:\.\d+)?\s*[\$€£¥₹]?\s*(?:[KkMmBbTt%]|thousand|million|billion|trillion|percent)?)",
            re.IGNORECASE,
        ),
    ]

    def __init__(
        self,
        value_parser: FinancialValueParserProtocol | None = None,
        period_normalizer: PeriodNormalizerProtocol | None = None,
    ) -> None:
        self.value_parser = value_parser or FinancialValueParser()
        self.period_normalizer = period_normalizer or FiscalPeriodNormalizer()

    def _parse_markdown_table_facts(
        self,
        evidence: RankedEvidence,
    ) -> list[FinancialFact]:
        """Extract structured facts from markdown table formatted evidence."""
        facts: list[FinancialFact] = []
        lines = [ln.strip() for ln in evidence.content.split("\n") if ln.strip()]
        table_lines = [ln for ln in lines if ln.startswith("|") and ln.endswith("|")]
        if len(table_lines) < 3:
            return facts

        # Parse context from surrounding title / headers
        currency = self.value_parser.detect_currency(evidence.content, default="USD")
        scale = self.value_parser.detect_scale_from_text(evidence.content)

        # Parse header columns
        raw_headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
        # Skip separator line (line 1)
        data_rows = table_lines[2:]

        # Map header columns to FiscalPeriod
        col_periods = []
        for h in raw_headers:
            norm_period = self.period_normalizer.normalize(h, default_year=evidence.fiscal_year)
            col_periods.append(norm_period)

        for row_str in data_rows:
            cells = [c.strip() for c in row_str.strip("|").split("|")]
            if not cells:
                continue

            row_label = cells[0].strip()
            # Clean up markdown formatting in row label
            row_label_clean = re.sub(r"[\*\_#]", "", row_label).strip()
            if not row_label_clean or row_label_clean.lower() in ("total", "subtotal", "---"):
                continue

            for col_idx in range(1, len(cells)):
                if col_idx >= len(col_periods):
                    break
                cell_text = cells[col_idx].strip()
                if not cell_text:
                    continue

                fin_val = self.value_parser.parse(
                    raw_str=cell_text,
                    context_currency=currency,
                    context_scale=scale.multiplier,
                )
                if fin_val is None:
                    continue

                period = col_periods[col_idx]
                fact_id = str(uuid4())
                facts.append(
                    FinancialFact(
                        fact_id=fact_id,
                        metric=row_label_clean,
                        value=fin_val,
                        period=period,
                        company=evidence.ticker or "Company",
                        ticker=evidence.ticker,
                        document_id=evidence.document_id,
                        document_version_id=evidence.document_version_id,
                        page_number=evidence.page_number,
                        chunk_id=str(evidence.chunk_id),
                        table_id=evidence.table_id,
                        source_evidence_id=str(evidence.chunk_id),
                        extraction_method="table_structured",
                        confidence=0.98,
                        source_text=f"{row_label_clean} | {raw_headers[col_idx]}: {cell_text}",
                        bounding_box=evidence.bounding_box,
                        section_path=evidence.section_path,
                        metadata={
                            "rank": evidence.rank,
                            "table_id": str(evidence.table_id) if evidence.table_id else None,
                        },
                    )
                )

        return facts

    def _parse_narrative_facts(
        self,
        evidence: RankedEvidence,
    ) -> list[FinancialFact]:
        """Extract structured financial facts from narrative text blocks."""
        facts: list[FinancialFact] = []
        sentences = re.split(r"(?<=[.!?])\s+", evidence.content)

        currency = self.value_parser.detect_currency(evidence.content, default="USD")
        scale = self.value_parser.detect_scale_from_text(evidence.content)

        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            # Pattern 1: Metric was Value in Period
            for pattern in self.NARRATIVE_PATTERNS:
                for match in pattern.finditer(sent_clean):
                    groups = match.groups()
                    if len(groups) == 3:
                        # Could be (metric, val, period) or (period, metric, val)
                        if any(
                            re.match(r"(?:fiscal|fy|20\d{2}|q[1-4])", str(g), re.I)
                            for g in [groups[0]]
                        ):
                            period_raw, metric_raw, val_raw = groups[0], groups[1], groups[2]
                        else:
                            metric_raw, val_raw, period_raw = groups[0], groups[1], groups[2]

                        metric_clean = re.sub(
                            r"^(?:the|our|total|consolidated)\s+",
                            "",
                            metric_raw.strip(),
                            flags=re.I,
                        ).strip()
                        # Validate that metric resembles a known financial term or has reasonable length
                        if len(metric_clean) < 3 or len(metric_clean) > 60:
                            continue

                        fin_val = self.value_parser.parse(
                            raw_str=val_raw,
                            context_currency=currency,
                            context_scale=scale.multiplier,
                        )
                        if fin_val is None:
                            continue

                        period = self.period_normalizer.normalize(
                            raw_period=period_raw or "",
                            default_year=evidence.fiscal_year,
                        )

                        fact_id = str(uuid4())
                        facts.append(
                            FinancialFact(
                                fact_id=fact_id,
                                metric=metric_clean.title(),
                                value=fin_val,
                                period=period,
                                company=evidence.ticker or "Company",
                                ticker=evidence.ticker,
                                document_id=evidence.document_id,
                                document_version_id=evidence.document_version_id,
                                page_number=evidence.page_number,
                                chunk_id=str(evidence.chunk_id),
                                table_id=evidence.table_id,
                                source_evidence_id=str(evidence.chunk_id),
                                extraction_method="narrative_regex",
                                confidence=0.85,
                                source_text=sent_clean,
                                bounding_box=evidence.bounding_box,
                                section_path=evidence.section_path,
                                metadata={"rank": evidence.rank},
                            )
                        )

        return facts

    def extract_facts(
        self,
        evidence_items: list[RankedEvidence],
    ) -> list[FinancialFact]:
        """Extract all verified FinancialFact instances across evidence items."""
        all_facts: list[FinancialFact] = []
        logger.info(f"Extracting structured facts from {len(evidence_items)} ranked evidence items")

        for item in evidence_items:
            # 1. If chunk is TABLE or contains markdown table syntax
            if item.chunk_type == ChunkType.TABLE or (
                "|" in item.content and "---" in item.content
            ):
                table_facts = self._parse_markdown_table_facts(item)
                all_facts.extend(table_facts)

            # 2. Extract narrative facts
            narrative_facts = self._parse_narrative_facts(item)
            all_facts.extend(narrative_facts)

        logger.info(f"Extracted {len(all_facts)} total financial facts")
        return all_facts
