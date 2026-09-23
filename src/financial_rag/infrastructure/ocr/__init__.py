"""OCR infrastructure package."""

from financial_rag.config.settings import ParserSettings, get_settings
from financial_rag.domain.interfaces.ocr import OCRAdapterProtocol, OCRResult
from financial_rag.infrastructure.ocr.mock_ocr import MockOCRAdapter
from financial_rag.infrastructure.ocr.tesseract import TesseractOCRAdapter


def get_ocr_adapter(parser_settings: ParserSettings | None = None) -> OCRAdapterProtocol:
    """Return configured OCR adapter instance."""
    settings = parser_settings or get_settings().parser
    if settings.ocr_provider == "tesseract":
        return TesseractOCRAdapter()
    return MockOCRAdapter()


__all__ = [
    "MockOCRAdapter",
    "OCRAdapterProtocol",
    "OCRResult",
    "TesseractOCRAdapter",
    "get_ocr_adapter",
]
