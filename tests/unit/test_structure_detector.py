"""Unit tests for FinancialStructureDetector."""

import pytest

from financial_rag.common.types import BlockType, DocumentType
from financial_rag.domain.entities.models import DocumentPage, LayoutBlock
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector


@pytest.mark.unit
def test_financial_structure_detector() -> None:
    detector = FinancialStructureDetector()

    page1 = DocumentPage(
        page_number=1,
        text_content="PART I\nITEM 1. BUSINESS\nAcme Corp is an AI company.",
        blocks=[
            LayoutBlock(id="b1", page_number=1, content="PART I", block_type=BlockType.TEXT),
            LayoutBlock(
                id="b2", page_number=1, content="ITEM 1. BUSINESS", block_type=BlockType.TEXT
            ),
            LayoutBlock(
                id="b3",
                page_number=1,
                content="Acme Corp is an AI company.",
                block_type=BlockType.TEXT,
            ),
        ],
    )

    page2 = DocumentPage(
        page_number=2,
        text_content="ITEM 8. FINANCIAL STATEMENTS\nCONSOLIDATED BALANCE SHEETS",
        blocks=[
            LayoutBlock(
                id="b4",
                page_number=2,
                content="ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA",
                block_type=BlockType.TEXT,
            ),
            LayoutBlock(
                id="b5",
                page_number=2,
                content="CONSOLIDATED BALANCE SHEETS",
                block_type=BlockType.TEXT,
            ),
        ],
    )

    detector.detect_structure([page1, page2], document_type=DocumentType.SEC_10K)

    # Check Page 1 tagged blocks
    assert page1.blocks[0].block_type == BlockType.HEADING
    assert "PART I" in page1.blocks[2].section_path
    assert "ITEM 1. BUSINESS" in page1.blocks[2].section_path

    # Check Page 2 tagged blocks
    assert "Consolidated Balance Sheets" in page2.blocks[1].section_path
