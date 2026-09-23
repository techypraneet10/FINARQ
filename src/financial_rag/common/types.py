"""Common utility types and primitives for Financial RAG Platform."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import NewType, TypeAlias


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


# Strong ID types for domain boundaries
DocumentId: TypeAlias = str
VersionId: TypeAlias = str
PageId: TypeAlias = str
ChunkId: TypeAlias = str
JobId: TypeAlias = str
BlockId: TypeAlias = str
TableId: TypeAlias = str
QueryId: TypeAlias = str
CitationId: TypeAlias = str


RequestId = NewType("RequestId", str)


class Environment(StrEnum):
    """Runtime execution environment."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DocumentType(StrEnum):
    """Supported financial document categories."""

    SEC_10K = "10-K"
    SEC_10Q = "10-Q"
    SEC_8K = "8-K"
    ANNUAL_REPORT = "annual_report"
    EARNINGS_CALL = "earnings_call"
    BANK_STATEMENT = "bank_statement"
    LOAN_AGREEMENT = "loan_agreement"
    FINANCIAL_STATEMENT = "financial_statement"
    OTHER = "other"


class IngestionStatus(StrEnum):
    """Lifecycle status of a document ingestion job."""

    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    COMPLETED = "completed"
    FAILED = "failed"


class IngestionStage(StrEnum):
    """Granular execution stage of document ingestion pipeline."""

    RECEIVED = "received"
    VALIDATING = "validating"
    STORED = "stored"
    QUEUED = "queued"
    PARSING = "parsing"
    OCR_PROCESSING = "ocr_processing"
    EXTRACTING_TABLES = "extracting_tables"
    NORMALIZING = "normalizing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDFType(StrEnum):
    """Detected PDF layout composition."""

    NATIVE_TEXT = "native_text"
    SCANNED_IMAGE = "scanned_image"
    HYBRID = "hybrid"


class ExtractionMethod(StrEnum):
    """Method used to extract text and layout from page."""

    NATIVE = "native"
    OCR = "ocr"
    HYBRID = "hybrid"


class BlockType(StrEnum):
    """Structural type of extracted layout block."""

    TEXT = "text"
    HEADING = "heading"
    TABLE = "table"
    LIST = "list"
    FOOTNOTE = "footnote"
    HEADER_FOOTER = "header_footer"
    OTHER = "other"


class ChunkType(StrEnum):
    """Category of generated document chunk."""

    TEXT = "text"
    TABLE = "table"
    SECTION_HEADER = "section_header"
    SUMMARY = "summary"
