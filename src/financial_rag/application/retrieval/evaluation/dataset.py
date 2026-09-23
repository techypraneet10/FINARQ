"""Curated financial retrieval evaluation benchmark dataset."""

from dataclasses import dataclass, field
from typing import Any

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import QueryType


@dataclass(frozen=True)
class BenchmarkItem:
    """A single evaluation query with ground-truth relevant evidence IDs and relevance grades."""

    query_id: str
    query_text: str
    query_type: QueryType
    expected_chunk_ids: list[str]
    relevance_grades: dict[
        str, float
    ]  # chunk_id -> relevance grade (e.g. 2.0 = highly relevant, 1.0 = relevant)
    description: str
    metadata_filters: dict[str, Any] = field(default_factory=dict)


def get_synthetic_financial_corpus() -> list[DocumentChunk]:
    """Generate synthetic financial document chunks representing SEC 10-K disclosures."""
    chunks: list[DocumentChunk] = []

    # 1. AAPL 2024 10-K - Financial Summary Table
    chunks.append(
        DocumentChunk(
            id="aapl-2024-chunk-101",
            document_id="doc-aapl-2024",
            document_version_id="ver-aapl-2024-v1",
            page_number=32,
            chunk_index=0,
            chunk_type=ChunkType.TABLE,
            content=(
                "| (In millions, except per share amounts) | 2024 | 2023 | 2022 |\n"
                "|---|---|---|---|\n"
                "| Total net sales | $391,035 | $383,285 | $394,328 |\n"
                "| Cost of sales | $210,352 | $214,137 | $223,546 |\n"
                "| Gross margin | $180,683 | $169,148 | $170,782 |\n"
                "| Operating expenses | $57,485 | $54,847 | $51,345 |\n"
                "| Operating income | $123,198 | $114,301 | $119,437 |\n"
                "| Net income | $93,736 | $96,995 | $99,803 |\n"
                "| Diluted earnings per share | $6.08 | $6.13 | $6.11 |"
            ),
            section_path="Item 8. Financial Statements > Consolidated Statements of Operations",
            table_id="table-aapl-income-2024",
            metadata={
                "ticker_symbol": "AAPL",
                "fiscal_year": 2024,
                "document_type": "10-K",
                "table_title": "Consolidated Statements of Operations",
            },
        )
    )

    # 2. AAPL 2024 10-K - Balance Sheet Table
    chunks.append(
        DocumentChunk(
            id="aapl-2024-chunk-102",
            document_id="doc-aapl-2024",
            document_version_id="ver-aapl-2024-v1",
            page_number=34,
            chunk_index=1,
            chunk_type=ChunkType.TABLE,
            content=(
                "| Consolidated Balance Sheets (In millions) | September 28, 2024 | September 30, 2023 |\n"
                "|---|---|---|\n"
                "| Cash and cash equivalents | $29,943 | $29,965 |\n"
                "| Marketable securities (current) | $35,217 | $31,590 |\n"
                "| Total current assets | $153,912 | $143,566 |\n"
                "| Property, plant and equipment, net | $45,246 | $43,715 |\n"
                "| Total assets | $364,980 | $352,583 |\n"
                "| Total current liabilities | $176,394 | $145,308 |\n"
                "| Total term debt | $97,428 | $105,096 |\n"
                "| Total liabilities | $308,030 | $290,437 |\n"
                "| Total shareholders' equity | $56,950 | $62,146 |"
            ),
            section_path="Item 8. Financial Statements > Consolidated Balance Sheets",
            table_id="table-aapl-balance-2024",
            metadata={
                "ticker_symbol": "AAPL",
                "fiscal_year": 2024,
                "document_type": "10-K",
                "table_title": "Consolidated Balance Sheets",
            },
        )
    )

    # 3. AAPL 2024 10-K - MD&A Narrative on Revenue Growth
    chunks.append(
        DocumentChunk(
            id="aapl-2024-chunk-103",
            document_id="doc-aapl-2024",
            document_version_id="ver-aapl-2024-v1",
            page_number=22,
            chunk_index=2,
            chunk_type=ChunkType.TEXT,
            content=(
                "Total net sales increased 2% or $7.8 billion during fiscal 2024 compared to fiscal 2023, "
                "driven primarily by higher Services net sales of $96.2 billion compared to $85.2 billion in 2023, "
                "and higher Mac net sales, partially offset by lower Wearables, Home and Accessories sales."
            ),
            section_path="Item 7. Management's Discussion and Analysis of Financial Condition > Net Sales",
            metadata={
                "ticker_symbol": "AAPL",
                "fiscal_year": 2024,
                "document_type": "10-K",
            },
        )
    )

    # 4. AAPL 2024 10-K - Product Segment Breakdown Table
    chunks.append(
        DocumentChunk(
            id="aapl-2024-chunk-104",
            document_id="doc-aapl-2024",
            document_version_id="ver-aapl-2024-v1",
            page_number=23,
            chunk_index=3,
            chunk_type=ChunkType.TABLE,
            content=(
                "| Net Sales by Product Category (In millions) | 2024 | 2023 | Change |\n"
                "|---|---|---|---|\n"
                "| iPhone | $201,183 | $200,583 | 0% |\n"
                "| Mac | $29,984 | $29,357 | 2% |\n"
                "| iPad | $26,694 | $28,300 | (6)% |\n"
                "| Wearables, Home and Accessories | $37,005 | $39,845 | (7)% |\n"
                "| Services | $96,169 | $85,200 | 13% |\n"
                "| Total net sales | $391,035 | $383,285 | 2% |"
            ),
            section_path="Item 7. MD&A > Segment Results",
            table_id="table-aapl-segments-2024",
            metadata={
                "ticker_symbol": "AAPL",
                "fiscal_year": 2024,
                "document_type": "10-K",
            },
        )
    )

    # 5. MSFT 2024 10-K - Risk Factors (Item 1A)
    chunks.append(
        DocumentChunk(
            id="msft-2024-chunk-201",
            document_id="doc-msft-2024",
            document_version_id="ver-msft-2024-v1",
            page_number=14,
            chunk_index=0,
            chunk_type=ChunkType.TEXT,
            content=(
                "ITEM 1A. RISK FACTORS. Our operations and financial results are subject to various risks and uncertainties. "
                "Key strategic risks include: intense competition in cloud computing (Azure) and artificial intelligence; "
                "cybersecurity vulnerabilities, system outages, and malicious attacks on our infrastructure; "
                "compliance with evolving global data privacy and artificial intelligence regulations; "
                "and risks associated with strategic investments, joint ventures, and acquisitions including Activision Blizzard."
            ),
            section_path="PART I > Item 1A. Risk Factors",
            metadata={
                "ticker_symbol": "MSFT",
                "fiscal_year": 2024,
                "document_type": "10-K",
            },
        )
    )

    # 6. MSFT 2024 10-K - Income Statement & Operating Income
    chunks.append(
        DocumentChunk(
            id="msft-2024-chunk-202",
            document_id="doc-msft-2024",
            document_version_id="ver-msft-2024-v1",
            page_number=45,
            chunk_index=1,
            chunk_type=ChunkType.TABLE,
            content=(
                "| Income Statements (In millions, except per share) | Year Ended June 30, 2024 | June 30, 2023 |\n"
                "|---|---|---|\n"
                "| Total revenue | $245,122 | $211,915 |\n"
                "| Cost of revenue | $74,102 | $65,863 |\n"
                "| Gross margin | $171,020 | $146,052 |\n"
                "| Research and development | $29,510 | $27,195 |\n"
                "| Sales and marketing | $25,230 | $22,759 |\n"
                "| General and administrative | $6,780 | $6,144 |\n"
                "| Operating income | $109,500 | $89,954 |\n"
                "| Net income | $88,136 | $72,361 |\n"
                "| Diluted earnings per share | $11.80 | $9.68 |"
            ),
            section_path="Item 8. Financial Statements > Income Statements",
            table_id="table-msft-income-2024",
            metadata={
                "ticker_symbol": "MSFT",
                "fiscal_year": 2024,
                "document_type": "10-K",
            },
        )
    )

    # 7. MSFT 2024 10-Q - Q3 Quarterly Revenue
    chunks.append(
        DocumentChunk(
            id="msft-2024-chunk-203",
            document_id="doc-msft-q3-2024",
            document_version_id="ver-msft-q3-2024-v1",
            page_number=8,
            chunk_index=0,
            chunk_type=ChunkType.TEXT,
            content=(
                "For the third quarter ended March 31, 2024 (Q3 FY24), Microsoft revenue was $61.9 billion, "
                "an increase of 17% compared to the corresponding period of the prior fiscal year. "
                "Operating income was $27.6 billion, up 23%, and diluted earnings per share was $2.94, up 20%."
            ),
            section_path="Part I. Financial Information > Item 2. Management's Discussion and Analysis",
            metadata={
                "ticker_symbol": "MSFT",
                "fiscal_year": 2024,
                "fiscal_period": "Q3",
                "document_type": "10-Q",
            },
        )
    )

    # 8. NVDA 2024 10-K - Revenue & Operating Income
    chunks.append(
        DocumentChunk(
            id="nvda-2024-chunk-301",
            document_id="doc-nvda-2024",
            document_version_id="ver-nvda-2024-v1",
            page_number=40,
            chunk_index=0,
            chunk_type=ChunkType.TABLE,
            content=(
                "| Consolidated Statements of Income (In millions) | Fiscal 2024 | Fiscal 2023 |\n"
                "|---|---|---|\n"
                "| Revenue | $60,922 | $26,974 |\n"
                "| Cost of revenue | $16,621 | $11,618 |\n"
                "| Gross profit | $44,301 | $15,356 |\n"
                "| Research and development | $8,675 | $7,339 |\n"
                "| Sales, general and administrative | $2,654 | $2,440 |\n"
                "| Operating income | $32,972 | $4,224 |\n"
                "| Net income | $29,760 | $4,368 |\n"
                "| Diluted earnings per share | $11.93 | $1.74 |"
            ),
            section_path="Item 8. Financial Statements > Consolidated Statements of Income",
            table_id="table-nvda-income-2024",
            metadata={
                "ticker_symbol": "NVDA",
                "fiscal_year": 2024,
                "document_type": "10-K",
            },
        )
    )

    # 9. AAPL 2024 10-K - Contractual Obligations & Leases
    chunks.append(
        DocumentChunk(
            id="aapl-2024-chunk-105",
            document_id="doc-aapl-2024",
            document_version_id="ver-aapl-2024-v1",
            page_number=28,
            chunk_index=4,
            chunk_type=ChunkType.TEXT,
            content=(
                "Note 10 - Commitments and Contingencies. The Company had total contractual obligations and "
                "operating lease liabilities of $11.4 billion as of September 28, 2024, of which $2.1 billion is due within 12 months. "
                "Manufacturing purchase obligations and commercial commitments totaled $34.8 billion."
            ),
            section_path="Item 8. Financial Statements > Note 10. Commitments and Contingencies",
            metadata={
                "ticker_symbol": "AAPL",
                "fiscal_year": 2024,
                "document_type": "10-K",
            },
        )
    )

    # 10. Accounting Principles / ASC 606 Revenue Recognition
    chunks.append(
        DocumentChunk(
            id="general-accounting-chunk-401",
            document_id="doc-general-accounting",
            document_version_id="ver-ga-v1",
            page_number=50,
            chunk_index=0,
            chunk_type=ChunkType.TEXT,
            content=(
                "Note 1 - Summary of Significant Accounting Policies. Revenue Recognition (ASC 606): "
                "The Company recognizes revenue when performance obligations under customer contracts are satisfied, "
                "which occurs when control of promised goods or services is transferred to the customer. "
                "Revenue is measured based on the consideration expected in exchange for those products."
            ),
            section_path="Item 8. Financial Statements > Note 1. Accounting Policies",
            metadata={
                "document_type": "10-K",
                "section": "Note 1. Accounting Policies",
            },
        )
    )

    return chunks


def get_benchmark_dataset() -> list[BenchmarkItem]:
    """Return standard 10-item curated retrieval evaluation benchmark."""
    return [
        # Query 1: Exact metric lookup
        BenchmarkItem(
            query_id="bench-01-exact-metric",
            query_text="What was Apple's total revenue in fiscal year 2024?",
            query_type=QueryType.FACTUAL,
            expected_chunk_ids=["aapl-2024-chunk-101", "aapl-2024-chunk-103"],
            relevance_grades={"aapl-2024-chunk-101": 2.0, "aapl-2024-chunk-103": 1.5},
            description="Exact lookup of AAPL 2024 net sales/revenue in financial statement and MD&A.",
        ),
        # Query 2: Multi-period comparison
        BenchmarkItem(
            query_id="bench-02-comparison",
            query_text="What was revenue growth from 2023 to 2024 for Apple?",
            query_type=QueryType.COMPARISON,
            expected_chunk_ids=["aapl-2024-chunk-103", "aapl-2024-chunk-101"],
            relevance_grades={"aapl-2024-chunk-103": 2.0, "aapl-2024-chunk-101": 1.5},
            description="Comparison query requiring 2023 and 2024 net sales and percentage change.",
        ),
        # Query 3: Section-specific lookup
        BenchmarkItem(
            query_id="bench-03-section-specific",
            query_text="What are the primary risk factors discussed in Item 1A for Microsoft?",
            query_type=QueryType.SECTION_SPECIFIC,
            expected_chunk_ids=["msft-2024-chunk-201"],
            relevance_grades={"msft-2024-chunk-201": 2.0},
            description="Section Item 1A Risk Factors retrieval for Microsoft.",
        ),
        # Query 4: Table lookup
        BenchmarkItem(
            query_id="bench-04-table-lookup",
            query_text="What were total assets on Apple's Consolidated Balance Sheet in 2024?",
            query_type=QueryType.TABLE_LOOKUP,
            expected_chunk_ids=["aapl-2024-chunk-102"],
            relevance_grades={"aapl-2024-chunk-102": 2.0},
            description="Table-specific lookup on AAPL Consolidated Balance Sheet.",
        ),
        # Query 5: Fiscal period lookup
        BenchmarkItem(
            query_id="bench-05-fiscal-period",
            query_text="What was Microsoft's revenue in Q3 2024?",
            query_type=QueryType.FACTUAL,
            expected_chunk_ids=["msft-2024-chunk-203"],
            relevance_grades={"msft-2024-chunk-203": 2.0},
            description="Quarterly financial inquiry for Microsoft Q3 FY24.",
        ),
        # Query 6: Company-specific inquiry
        BenchmarkItem(
            query_id="bench-06-company-specific",
            query_text="What was NVIDIA's operating income in fiscal 2024?",
            query_type=QueryType.FACTUAL,
            expected_chunk_ids=["nvda-2024-chunk-301"],
            relevance_grades={"nvda-2024-chunk-301": 2.0},
            description="Operating income lookup for NVDA 2024.",
        ),
        # Query 7: Multi-document inquiry
        BenchmarkItem(
            query_id="bench-07-multi-document",
            query_text="Compare total revenue between Apple and Microsoft in 2024.",
            query_type=QueryType.MULTI_DOCUMENT,
            expected_chunk_ids=["aapl-2024-chunk-101", "msft-2024-chunk-202"],
            relevance_grades={"aapl-2024-chunk-101": 2.0, "msft-2024-chunk-202": 2.0},
            description="Cross-company comparison across AAPL and MSFT 10-K filings.",
        ),
        # Query 8: Terminology-heavy query
        BenchmarkItem(
            query_id="bench-08-terminology",
            query_text="What were the contractual obligations, commercial commitments, and operating lease liabilities?",
            query_type=QueryType.FACTUAL,
            expected_chunk_ids=["aapl-2024-chunk-105"],
            relevance_grades={"aapl-2024-chunk-105": 2.0},
            description="Terminology-rich commitments and lease obligations lookup.",
        ),
        # Query 9: Segment breakdown table
        BenchmarkItem(
            query_id="bench-09-segment-breakdown",
            query_text="What was Apple's Services revenue compared to iPhone revenue in 2024?",
            query_type=QueryType.TABLE_LOOKUP,
            expected_chunk_ids=["aapl-2024-chunk-104", "aapl-2024-chunk-101"],
            relevance_grades={"aapl-2024-chunk-104": 2.0, "aapl-2024-chunk-101": 1.0},
            description="Product segment breakdown table lookup for Apple.",
        ),
        # Query 10: Definition / Policy
        BenchmarkItem(
            query_id="bench-10-definition-policy",
            query_text="What is the revenue recognition policy under ASC 606?",
            query_type=QueryType.DEFINITION,
            expected_chunk_ids=["general-accounting-chunk-401"],
            relevance_grades={"general-accounting-chunk-401": 2.0},
            description="Accounting standard definition and policy disclosure.",
        ),
    ]
