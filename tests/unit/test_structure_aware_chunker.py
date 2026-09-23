"""Unit tests for StructureAwareChunker."""

import pytest

from financial_rag.common.types import BlockType, ChunkType
from financial_rag.config.settings import ChunkingSettings
from financial_rag.domain.entities.models import (
    DocumentPage,
    FinancialTable,
    LayoutBlock,
)
from financial_rag.infrastructure.chunking.structure_aware import StructureAwareChunker


@pytest.mark.unit
def test_structure_aware_chunker_preserves_tables_and_sections() -> None:
    settings = ChunkingSettings(max_chunk_size=300)
    chunker = StructureAwareChunker(chunking_settings=settings)

    page1 = DocumentPage(
        page_number=1,
        text_content="Page 1 narrative",
        blocks=[
            LayoutBlock(
                id="b1",
                page_number=1,
                block_type=BlockType.TEXT,
                content="Item 1 Business narrative line 1.",
                section_path="Part I > Item 1. Business",
            ),
            LayoutBlock(
                id="b2",
                page_number=1,
                block_type=BlockType.TEXT,
                content="Item 1 Business narrative line 2.",
                section_path="Part I > Item 1. Business",
            ),
            LayoutBlock(
                id="b3",
                page_number=1,
                block_type=BlockType.TEXT,
                content="Item 1A Risk Factors line 1.",
                section_path="Part I > Item 1A. Risk Factors",
            ),
        ],
        tables=[
            FinancialTable(
                id="tbl-100",
                page_number=1,
                title="Balance Sheet",
                headers=["Asset", "Value"],
                rows=[["Cash", "$500"]],
                markdown_repr="| Asset | Value |\n| Cash | $500 |",
            )
        ],
    )

    chunks = chunker.chunk_document(
        document_id="doc-999",
        version_id="ver-999",
        pages=[page1],
    )

    assert len(chunks) >= 3

    # Check dedicated table chunk
    table_chunks = [c for c in chunks if c.chunk_type == ChunkType.TABLE]
    assert len(table_chunks) == 1
    assert table_chunks[0].table_id == "tbl-100"
    assert "| Asset | Value |" in table_chunks[0].content
    assert table_chunks[0].document_id == "doc-999"
    assert table_chunks[0].document_version_id == "ver-999"

    # Check text chunks preserve distinct sections without blending
    text_chunks = [c for c in chunks if c.chunk_type == ChunkType.TEXT]
    item1_chunks = [c for c in text_chunks if "Item 1. Business" in c.section_path]
    item1a_chunks = [c for c in text_chunks if "Item 1A. Risk Factors" in c.section_path]

    assert len(item1_chunks) >= 1
    assert len(item1a_chunks) >= 1
    assert "Risk Factors" not in item1_chunks[0].content
