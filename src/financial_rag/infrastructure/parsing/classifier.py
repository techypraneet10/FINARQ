"""PDF layout classifier detecting native text, scanned image, or hybrid document types."""

import io

from financial_rag.common.types import PDFType
from financial_rag.config.settings import ParserSettings, get_settings
from financial_rag.domain.interfaces.parser import PDFClassifierProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.parsing.classifier")


class PDFClassifier(PDFClassifierProtocol):
    """Classifies PDF documents by analyzing text density and image coverage."""

    def __init__(self, parser_settings: ParserSettings | None = None) -> None:
        self._settings = parser_settings or get_settings().parser

    def classify(self, content: bytes) -> PDFType:
        """Classify PDF as NATIVE_TEXT, SCANNED_IMAGE, or HYBRID."""
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=content, filetype="pdf")
            total_pages = len(doc)
            if total_pages == 0:
                return PDFType.NATIVE_TEXT

            text_page_count = 0
            scanned_page_count = 0

            for page_idx in range(total_pages):
                page = doc[page_idx]
                text = page.get_text().strip()
                char_count = len(text)

                if char_count >= self._settings.ocr_char_threshold:
                    text_page_count += 1
                else:
                    # Check if page has images
                    image_list = page.get_images()
                    if image_list or char_count < 10:
                        scanned_page_count += 1
                    else:
                        text_page_count += 1

            doc.close()

            if scanned_page_count == total_pages:
                return PDFType.SCANNED_IMAGE
            elif text_page_count == total_pages:
                return PDFType.NATIVE_TEXT
            else:
                return PDFType.HYBRID

        except Exception as ex:
            logger.warning(
                f"PyMuPDF classification failed ({ex}), falling back to pypdf inspection"
            )
            return self._classify_with_pypdf(content)

    def _classify_with_pypdf(self, content: bytes) -> PDFType:
        """Fallback classification using pure Python pypdf."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(content))
            total_pages = len(reader.pages)
            if total_pages == 0:
                return PDFType.NATIVE_TEXT

            total_chars = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                total_chars += len(text.strip())

            avg_chars_per_page = total_chars / total_pages
            if avg_chars_per_page < self._settings.ocr_char_threshold:
                return PDFType.SCANNED_IMAGE
            return PDFType.NATIVE_TEXT
        except Exception:
            return PDFType.NATIVE_TEXT
