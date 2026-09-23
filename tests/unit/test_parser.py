"""Unit tests for PDF classifier and PyMuPDF layout-aware parser."""

import pytest

from financial_rag.common.types import PDFType
from financial_rag.infrastructure.ocr.mock_ocr import MockOCRAdapter
from financial_rag.infrastructure.parsing.classifier import PDFClassifier
from financial_rag.infrastructure.parsing.pdf_parser import PyMuPDFParser
from tests.fixtures.pdf_fixtures import (
    create_sample_10k_pdf,
    create_scanned_image_pdf,
)


@pytest.mark.unit
def test_pdf_classifier() -> None:
    classifier = PDFClassifier()

    native_pdf = create_sample_10k_pdf()
    assert classifier.classify(native_pdf) == PDFType.NATIVE_TEXT

    scanned_pdf = create_scanned_image_pdf()
    assert classifier.classify(scanned_pdf) == PDFType.SCANNED_IMAGE


@pytest.mark.unit
async def test_pymupdf_parser_native_pdf() -> None:
    parser = PyMuPDFParser()
    pdf_bytes = create_sample_10k_pdf()

    parsed = await parser.parse(pdf_bytes, filename="sample_10k.pdf")
    assert parsed.total_pages == 3
    assert len(parsed.pages) == 3

    # Verify Page 1
    page1 = parsed.pages[0]
    assert page1.page_number == 1
    assert "ACME FINANCIAL CORP." in page1.text_content
    assert len(page1.blocks) > 0
    # Check bounding box presence
    assert page1.blocks[0].bounding_box is not None
    assert page1.blocks[0].bounding_box.width > 0

    # Verify Page 2 (with table)
    page2 = parsed.pages[1]
    assert page2.page_number == 2
    assert "CONSOLIDATED BALANCE SHEETS" in page2.text_content

    # Verify Page 3
    page3 = parsed.pages[2]
    assert "NOTES TO CONSOLIDATED FINANCIAL STATEMENTS" in page3.text_content


@pytest.mark.unit
async def test_mock_ocr_adapter() -> None:
    ocr = MockOCRAdapter()
    res = await ocr.ocr_page(b"fake_image_bytes", page_number=2)
    assert res.confidence == 0.98
    assert len(res.text) > 0
    assert len(res.blocks) > 0
