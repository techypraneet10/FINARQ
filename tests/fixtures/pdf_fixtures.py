"""Synthetic financial PDF fixture generators for automated testing."""

import io

import fitz  # PyMuPDF
from PIL import Image, ImageDraw


def create_sample_10k_pdf() -> bytes:
    """Generate a multi-page SEC 10-K synthetic PDF with structured items and financial tables."""
    doc = fitz.open()

    # Page 1: Cover & Item 1. Business
    page1 = doc.new_page(width=612, height=792)
    p1_text = (
        "UNITED STATES SECURITIES AND EXCHANGE COMMISSION\n"
        "Washington, D.C. 20549\n"
        "FORM 10-K\n\n"
        "ACME FINANCIAL CORP.\n"
        "PART I\n\n"
        "ITEM 1. BUSINESS\n"
        "Acme Financial Corp. is a global enterprise software and financial services company. "
        "Our core mission is delivering mission-critical analytics and automated RAG systems to Tier-1 financial institutions.\n\n"
        "ITEM 1A. RISK FACTORS\n"
        "Our business is subject to complex regulatory frameworks, macroeconomic volatility, and technological shifts. "
        "Adverse macroeconomic changes could reduce institutional software spending."
    )
    page1.insert_text((50, 50), p1_text, fontsize=11)

    # Page 2: Item 7. MD&A and Item 8. Financial Statements (with table)
    page2 = doc.new_page(width=612, height=792)
    p2_text = (
        "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION\n"
        "Total revenue grew by 18.5% year-over-year driven by cloud expansion.\n\n"
        "ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA\n"
        "CONSOLIDATED BALANCE SHEETS\n"
        "(In millions, except share amounts)\n"
    )
    page2.insert_text((50, 50), p2_text, fontsize=11)

    # Insert multi-column tabular block for balance sheet
    table_block_text = (
        "Assets                              December 31, 2023    December 31, 2022\n"
        "Cash and cash equivalents           $ 28,150             $ 24,680\n"
        "Marketable securities               31,540               26,110\n"
        "Unrealized investment loss          (1,234.50)           (850.00)\n"
        "Total Current Assets                $ 58,455.50          $ 49,940.00"
    )
    page2.insert_text((50, 180), table_block_text, fontsize=10)

    # Page 3: Notes to Financial Statements
    page3 = doc.new_page(width=612, height=792)
    p3_text = (
        "NOTES TO CONSOLIDATED FINANCIAL STATEMENTS\n"
        "Note 1. Summary of Significant Accounting Policies\n"
        "The accompanying consolidated financial statements have been prepared in conformity with US GAAP.\n"
        "Note 2. Revenue Recognition\n"
        "Revenue is recognized when control of the promised goods or services is transferred to customers."
    )
    page3.insert_text((50, 50), p3_text, fontsize=11)

    pdf_bytes: bytes = bytes(doc.write())
    doc.close()
    return pdf_bytes


def create_scanned_image_pdf() -> bytes:
    """Generate a PDF containing an image of text without a native text layer (scanned document)."""
    # Create PIL image with financial statement text
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((50, 50), "SCANNED ANNUAL AUDIT REPORT", fill=(0, 0, 0))
    draw.text((50, 90), "Independent Auditor Report for Fiscal Year 2023", fill=(0, 0, 0))
    draw.text(
        (50, 130), "We have audited the consolidated balance sheets of Acme Corp.", fill=(0, 0, 0)
    )

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="PNG")
    img_bytes = img_byte_arr.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    rect = fitz.Rect(0, 0, 612, 792)
    page.insert_image(rect, stream=img_bytes)

    pdf_bytes: bytes = bytes(doc.write())
    doc.close()
    return pdf_bytes


def create_corrupt_pdf() -> bytes:
    """Generate corrupt / invalid PDF bytes."""
    return b"%PDF-1.7 corrupt invalid payload without xref table or valid dictionary"
