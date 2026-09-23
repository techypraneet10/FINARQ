"""Layout-aware PDF parsing engine using PyMuPDF (fitz) with OCR fallback."""

import io
from uuid import uuid4

from financial_rag.common.types import (
    BlockId,
    BlockType,
    ExtractionMethod,
    PDFType,
    TableId,
)
from financial_rag.config.settings import ParserSettings, get_settings
from financial_rag.domain.entities.models import (
    DocumentPage,
    FinancialTable,
    LayoutBlock,
)
from financial_rag.domain.entities.value_objects import BoundingBox, TableCell
from financial_rag.domain.exceptions import DocumentParsingError
from financial_rag.domain.interfaces.ocr import OCRAdapterProtocol
from financial_rag.domain.interfaces.parser import (
    ParsedDocument,
    PDFClassifierProtocol,
    PDFParserProtocol,
)
from financial_rag.infrastructure.logging import get_logger
from financial_rag.infrastructure.ocr import get_ocr_adapter
from financial_rag.infrastructure.parsing.classifier import PDFClassifier

logger = get_logger("financial_rag.infrastructure.parsing.pdf_parser")


class PyMuPDFParser(PDFParserProtocol):
    """Production layout-aware PDF parser that extracts text, blocks, tables, and coordinates."""

    def __init__(
        self,
        classifier: PDFClassifierProtocol | None = None,
        ocr_adapter: OCRAdapterProtocol | None = None,
        parser_settings: ParserSettings | None = None,
    ) -> None:
        self._settings = parser_settings or get_settings().parser
        self._classifier = classifier or PDFClassifier(self._settings)
        self._ocr_adapter = ocr_adapter or get_ocr_adapter(self._settings)

    async def parse(self, content: bytes, filename: str = "") -> ParsedDocument:
        """Parse PDF binary into structured pages, layout blocks, and tables."""
        if not content:
            raise DocumentParsingError("Cannot parse empty PDF byte buffer.")

        pdf_type = self._classifier.classify(content)
        logger.info(f"Parsing PDF '{filename}' classified as [{pdf_type.value}]")

        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=content, filetype="pdf")
            total_pages = len(doc)
            pages: list[DocumentPage] = []

            for page_idx in range(total_pages):
                page_num = page_idx + 1
                page = doc[page_idx]
                p_width = float(page.rect.width)
                p_height = float(page.rect.height)

                raw_text = page.get_text().strip()
                blocks: list[LayoutBlock] = []
                tables: list[FinancialTable] = []
                extraction_method = ExtractionMethod.NATIVE

                # 1. Extract Native Tables (PyMuPDF TableFinder)
                table_bboxes: list[BoundingBox] = []
                try:
                    tabs = page.find_tables()
                    for t_idx, tab in enumerate(tabs):
                        t_rect = tab.bbox
                        t_bbox = BoundingBox(
                            x0=float(t_rect[0]),
                            y0=float(t_rect[1]),
                            x1=float(t_rect[2]),
                            y1=float(t_rect[3]),
                            page_width=p_width,
                            page_height=p_height,
                        )
                        table_bboxes.append(t_bbox)

                        df_data = tab.extract()
                        if df_data and len(df_data) > 0:
                            raw_headers = [str(h or "").strip() for h in df_data[0]]
                            raw_rows = [
                                [str(cell or "").strip() for cell in row] for row in df_data[1:]
                            ]
                            cells: list[TableCell] = []
                            for r_i, row in enumerate(df_data):
                                is_hdr = r_i == 0
                                for c_i, cell in enumerate(row):
                                    cell_str = str(cell or "").strip()
                                    cells.append(
                                        TableCell(
                                            row_index=r_i,
                                            col_index=c_i,
                                            text=cell_str,
                                            is_header=is_hdr,
                                        )
                                    )

                            table_id: TableId = str(uuid4())
                            tables.append(
                                FinancialTable(
                                    id=table_id,
                                    page_number=page_num,
                                    title=f"Table {t_idx + 1} (Page {page_num})",
                                    headers=raw_headers,
                                    rows=raw_rows,
                                    cells=cells,
                                    bounding_box=t_bbox,
                                )
                            )
                except Exception as ex:
                    logger.debug(f"TableFinder on page {page_num} notice: {ex}")

                # 2. Extract Layout Blocks
                text_dict = page.get_text("dict")
                reading_order = 1

                for b in text_dict.get("blocks", []):
                    # Check if block is image or text
                    if b.get("type") == 0:  # Text block
                        b_bbox = BoundingBox(
                            x0=float(b["bbox"][0]),
                            y0=float(b["bbox"][1]),
                            x1=float(b["bbox"][2]),
                            y1=float(b["bbox"][3]),
                            page_width=p_width,
                            page_height=p_height,
                        )

                        # Determine if block overlaps an extracted table
                        is_inside_table = any(
                            b_bbox.x0 >= tb.x0 - 5
                            and b_bbox.x1 <= tb.x1 + 5
                            and b_bbox.y0 >= tb.y0 - 5
                            and b_bbox.y1 <= tb.y1 + 5
                            for tb in table_bboxes
                        )

                        # Aggregate block lines
                        block_lines: list[str] = []
                        max_font_size = 0.0
                        is_bold = False

                        for line in b.get("lines", []):
                            line_spans = []
                            for span in line.get("spans", []):
                                line_spans.append(span.get("text", ""))
                                font_size = float(span.get("size", 10.0))
                                if font_size > max_font_size:
                                    max_font_size = font_size
                                font_flags = span.get("flags", 0)
                                if font_flags & 2 != 0 or "bold" in span.get("font", "").lower():
                                    is_bold = True
                            block_lines.append(" ".join(line_spans))

                        block_content = "\n".join(block_lines).strip()
                        if not block_content:
                            continue

                        # Classify block type
                        if is_inside_table:
                            block_type = BlockType.TABLE
                        elif max_font_size >= 13.0 or (is_bold and max_font_size >= 11.0):
                            block_type = BlockType.HEADING
                        else:
                            block_type = BlockType.TEXT

                        block_id: BlockId = str(uuid4())
                        blocks.append(
                            LayoutBlock(
                                id=block_id,
                                page_number=page_num,
                                block_type=block_type,
                                content=block_content,
                                reading_order=reading_order,
                                bounding_box=b_bbox,
                                font_size=max_font_size if max_font_size > 0 else None,
                                is_bold=is_bold,
                                source_method=ExtractionMethod.NATIVE,
                            )
                        )
                        reading_order += 1

                # 3. Check for Scanned / Image-heavy page needing OCR
                has_images = len(page.get_images()) > 0
                if len(raw_text) < self._settings.ocr_char_threshold and self._settings.ocr_enabled:
                    logger.info(
                        f"Page {page_num} character density ({len(raw_text)}) below threshold, triggering OCR"
                    )
                    try:
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        ocr_result = await self._ocr_adapter.ocr_page(
                            img_bytes, page_number=page_num
                        )
                        if ocr_result.text and len(ocr_result.text) > len(raw_text):
                            raw_text = ocr_result.text
                            if not blocks:
                                blocks = ocr_result.blocks
                            extraction_method = ExtractionMethod.OCR
                    except Exception as ocr_ex:
                        logger.warning(f"OCR fallback failed for page {page_num}: {ocr_ex}")

                doc_page = DocumentPage(
                    id=str(uuid4()),
                    page_number=page_num,
                    text_content=raw_text,
                    blocks=blocks,
                    tables=tables,
                    extraction_method=extraction_method,
                    has_images=has_images,
                    width=p_width,
                    height=p_height,
                    metadata={"page_index": page_idx, "filename": filename},
                )
                pages.append(doc_page)

            doc.close()
            return ParsedDocument(
                pages=pages,
                pdf_type=pdf_type,
                total_pages=len(pages),
                metadata={"filename": filename, "parser": "PyMuPDF"},
            )

        except ImportError:
            logger.warning("PyMuPDF not installed, falling back to pypdf parser")
            return await self._parse_with_pypdf(content, filename, pdf_type)
        except Exception as ex:
            logger.error(f"PyMuPDF parser error: {ex}")
            raise DocumentParsingError(
                message=f"Failed to parse PDF document '{filename}': {ex}",
                details={"filename": filename, "error": str(ex)},
            ) from ex

    async def _parse_with_pypdf(
        self, content: bytes, filename: str, pdf_type: PDFType
    ) -> ParsedDocument:
        """Pure Python fallback parser using pypdf."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            pages: list[DocumentPage] = []

            for idx, page in enumerate(reader.pages):
                page_num = idx + 1
                text = page.extract_text() or ""
                block_id: BlockId = str(uuid4())
                block = LayoutBlock(
                    id=block_id,
                    page_number=page_num,
                    block_type=BlockType.TEXT,
                    content=text.strip(),
                    reading_order=1,
                    source_method=ExtractionMethod.NATIVE,
                )
                pages.append(
                    DocumentPage(
                        id=str(uuid4()),
                        page_number=page_num,
                        text_content=text.strip(),
                        blocks=[block] if text.strip() else [],
                        extraction_method=ExtractionMethod.NATIVE,
                        metadata={"page_index": idx, "filename": filename, "fallback": "pypdf"},
                    )
                )

            return ParsedDocument(
                pages=pages,
                pdf_type=pdf_type,
                total_pages=len(pages),
                metadata={"filename": filename, "parser": "pypdf"},
            )
        except Exception as ex:
            raise DocumentParsingError(
                message=f"Fallback pypdf parser failed for '{filename}': {ex}",
                details={"filename": filename, "error": str(ex)},
            ) from ex
