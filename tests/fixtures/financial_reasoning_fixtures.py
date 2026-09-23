"""Test fixtures and synthetic datasets for Phase 3 financial reasoning and grounding."""

from uuid import uuid4

from financial_rag.common.types import ChunkType
from financial_rag.domain.entities.retrieval import RankedEvidence, RetrievalSource
from financial_rag.domain.entities.value_objects import ProvenanceLineage


def make_test_evidence(
    content: str,
    chunk_type: ChunkType = ChunkType.TEXT,
    page_number: int = 1,
    document_id: str = "doc-apple-2024",
    ticker: str = "AAPL",
    fiscal_year: int = 2024,
    fiscal_period: str = "FY",
    table_id: str | None = None,
    rank: int = 1,
) -> RankedEvidence:
    """Helper creating a valid RankedEvidence test instance with complete provenance."""
    chunk_id = f"chunk-{uuid4()}"
    prov = ProvenanceLineage(
        document_id=document_id,
        document_version_id="ver-001",
        page_numbers=[page_number],
        source_block_ids=["block-001"],
        section_path="Item 8 > Financial Statements",
        chunk_type=chunk_type.value,
        table_id=table_id,
        chunk_id=chunk_id,
    )

    return RankedEvidence(
        rank=rank,
        chunk_id=chunk_id,
        document_id=document_id,
        document_version_id="ver-001",
        page_number=page_number,
        page_numbers=[page_number],
        chunk_type=chunk_type,
        content=content,
        section_path="Item 8 > Financial Statements",
        table_id=table_id,
        source_block_ids=["block-001"],
        bounding_box={"x0": 50.0, "y0": 100.0, "x1": 550.0, "y1": 400.0},
        content_hash="hash-123456",
        ticker=ticker,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        retrieval_sources=[RetrievalSource.BOTH],
        dense_score=0.92,
        sparse_score=0.88,
        fusion_score=0.95,
        reranker_score=0.96,
        final_score=0.96,
        provenance=prov,
    )


def make_sample_apple_table_evidence() -> RankedEvidence:
    """Sample Apple Inc. Income Statement Table Evidence in Markdown format."""
    table_content = """### Consolidated Statements of Operations (in millions, except per share amounts)
| Metric | 2024 | 2023 | 2022 |
| --- | --- | --- | --- |
| Total net sales | 391,035 | 383,285 | 394,328 |
| Cost of sales | (210,352) | (214,137) | (223,546) |
| Gross margin | 180,683 | 169,148 | 170,782 |
| Operating expenses | (57,466) | (54,847) | (51,345) |
| Operating income | 123,217 | 114,301 | 119,437 |
| Net income | 93,736 | 96,995 | 99,803 |
"""
    return make_test_evidence(
        content=table_content,
        chunk_type=ChunkType.TABLE,
        page_number=45,
        document_id="doc-aapl-10k-2024",
        ticker="AAPL",
        fiscal_year=2024,
        table_id="tbl-ops-2024",
        rank=1,
    )


def make_sample_apple_narrative_evidence() -> RankedEvidence:
    """Sample Apple Inc. MD&A Narrative Evidence."""
    narrative_content = (
        "During fiscal year 2024, total net sales were $391.0 billion, representing an increase "
        "compared to fiscal year 2023. Operating income reached $123.2 billion in 2024, driven by "
        "services revenue expansion. Research and development expenses were $31.4 billion for 2024."
    )
    return make_test_evidence(
        content=narrative_content,
        chunk_type=ChunkType.TEXT,
        page_number=30,
        document_id="doc-aapl-10k-2024",
        ticker="AAPL",
        fiscal_year=2024,
        rank=2,
    )


def make_sample_conflicting_narrative_evidence() -> RankedEvidence:
    """Sample narrative claiming a conflicting net income value ($90.0 billion vs $93.736 billion)."""
    conflict_content = "In fiscal year 2024, consolidated net income was $90.0 billion due to one-time restructuring charges."
    return make_test_evidence(
        content=conflict_content,
        chunk_type=ChunkType.TEXT,
        page_number=32,
        document_id="doc-aapl-10k-2024",
        ticker="AAPL",
        fiscal_year=2024,
        rank=3,
    )
