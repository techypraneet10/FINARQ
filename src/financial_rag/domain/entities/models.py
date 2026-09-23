"""Domain entities representing core concepts in Financial Document Intelligence.

These models encapsulate pure business logic and contracts.
They must remain independent of databases, web frameworks, vector stores, and external APIs.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from financial_rag.common.types import (
    BlockId,
    BlockType,
    ChunkId,
    ChunkType,
    CitationId,
    DocumentId,
    DocumentType,
    ExtractionMethod,
    IngestionStage,
    IngestionStatus,
    JobId,
    PageId,
    QueryId,
    TableId,
    VersionId,
)
from financial_rag.domain.entities.value_objects import (
    BoundingBox,
    ProvenanceLineage,
    TableCell,
)


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


@dataclass(frozen=True)
class User:
    """User account entity."""

    id: str
    email: str
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class LayoutBlock:
    """A single layout block on a document page (text, heading, table, list, etc.)."""

    id: BlockId
    page_number: int
    block_type: BlockType
    content: str
    reading_order: int = 0
    bounding_box: BoundingBox | None = None
    confidence: float = 1.0
    section_path: str = ""
    font_size: float | None = None
    is_bold: bool = False
    source_method: ExtractionMethod = ExtractionMethod.NATIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert block to dictionary representation."""
        return {
            "id": str(self.id),
            "page_number": self.page_number,
            "block_type": self.block_type.value,
            "content": self.content,
            "reading_order": self.reading_order,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "confidence": self.confidence,
            "section_path": self.section_path,
            "font_size": self.font_size,
            "is_bold": self.is_bold,
            "source_method": self.source_method.value,
            "metadata": self.metadata,
        }


@dataclass
class FinancialTable:
    """Normalized representation of a financial table preserving headers, numbers, and units."""

    id: TableId
    page_number: int
    title: str = ""
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    cells: list[TableCell] = field(default_factory=list)
    units: str = ""  # e.g., "in millions", "thousands", "ratio"
    currency: str = "USD"  # e.g., "$", "USD", "EUR"
    scale: float = 1.0  # multiplier (e.g. 1,000,000 for millions)
    footnotes: list[str] = field(default_factory=list)
    bounding_box: BoundingBox | None = None
    markdown_repr: str = ""
    csv_repr: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert table to dictionary representation."""
        return {
            "id": str(self.id),
            "page_number": self.page_number,
            "title": self.title,
            "headers": self.headers,
            "rows": self.rows,
            "units": self.units,
            "currency": self.currency,
            "scale": self.scale,
            "footnotes": self.footnotes,
            "bounding_box": self.bounding_box.to_dict() if self.bounding_box else None,
            "markdown_repr": self.markdown_repr,
            "metadata": self.metadata,
        }


@dataclass
class DocumentPage:
    """A single page extracted from a document with structural layout."""

    page_number: int
    text_content: str
    id: PageId = field(default_factory=lambda: str(uuid4()))
    document_id: DocumentId = ""
    version_id: VersionId = ""
    tenant_id: str = "default_tenant"
    blocks: list[LayoutBlock] = field(default_factory=list)
    tables: list[FinancialTable] = field(default_factory=list)
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE
    has_images: bool = False
    confidence: float = 1.0
    width: float = 0.0
    height: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """A deterministic, semantically coherent segment of a document page."""

    id: ChunkId
    document_id: DocumentId
    page_number: int
    content: str
    chunk_index: int
    document_version_id: VersionId = ""
    tenant_id: str = "default_tenant"
    page_numbers: list[int] = field(default_factory=list)
    chunk_type: ChunkType = ChunkType.TEXT
    source_block_ids: list[BlockId] = field(default_factory=list)
    section_path: str = ""
    table_id: TableId | None = None
    token_count: int = 0
    char_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        """Ensure page_numbers list contains primary page_number."""
        if not self.page_numbers and self.page_number:
            self.page_numbers = [self.page_number]
        if not self.char_count and self.content:
            self.char_count = len(self.content)

    def get_provenance(self) -> ProvenanceLineage:
        """Construct full provenance lineage object."""
        return ProvenanceLineage(
            document_id=self.document_id,
            document_version_id=self.document_version_id,
            page_numbers=self.page_numbers or [self.page_number],
            source_block_ids=self.source_block_ids,
            section_path=self.section_path,
            chunk_type=self.chunk_type.value,
            table_id=self.table_id,
            chunk_id=self.id,
        )


@dataclass
class DocumentVersion:
    """Immutable version snapshot of a document in storage."""

    version_number: int
    storage_uri: str
    file_hash_sha256: str
    id: VersionId = field(default_factory=lambda: str(uuid4()))
    document_id: DocumentId = ""
    tenant_id: str = "default_tenant"
    filename: str = ""
    file_size_bytes: int = 0
    mime_type: str = "application/pdf"
    pages_count: int = 0
    created_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Core financial document entity (e.g. SEC 10-K, 10-Q, Annual Report)."""

    id: DocumentId
    title: str
    document_type: DocumentType
    tenant_id: str = "default_tenant"
    ticker_symbol: str | None = None
    fiscal_year: int | None = None
    fiscal_period: str | None = None
    storage_uri: str = ""
    file_hash_sha256: str = ""
    pages_count: int = 0
    current_version_id: VersionId | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass
class IngestionJob:
    """State of an asynchronous document processing and ingestion job."""

    id: JobId
    document_id: DocumentId
    version_id: VersionId = ""
    tenant_id: str = "default_tenant"
    user_id: str | None = None
    status: IngestionStatus = IngestionStatus.PENDING
    current_stage: IngestionStage = IngestionStage.QUEUED
    progress_pct: float = 0.0
    chunks_indexed: int = 0
    error_message: str | None = None
    error_stage: IngestionStage | None = None
    error_details: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True)
class Query:
    """User inquiry targeted at financial documents."""

    id: QueryId
    text: str
    tenant_id: str = "default_tenant"
    user_id: str | None = None
    ticker_symbols: list[str] = field(default_factory=list)
    fiscal_years: list[int] = field(default_factory=list)
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class RetrievalResult:
    """A candidate chunk matched via vector or hybrid search."""

    chunk: DocumentChunk
    score: float
    retrieval_method: str  # e.g., 'dense_vector', 'bm25_sparse', 'hybrid'


@dataclass(frozen=True)
class Evidence:
    """Verified ground truth segment extracted for answering a query."""

    chunk_id: ChunkId
    document_id: DocumentId
    page_number: int
    exact_text: str
    tenant_id: str = "default_tenant"
    bounding_box: dict[str, float] | None = None


@dataclass(frozen=True)
class ReasoningStep:
    """Deterministic calculation or logical deduction step."""

    step_number: int
    description: str
    formula: str | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    output: Any = None


@dataclass(frozen=True)
class Citation:
    """Verifiable source citation pointing to specific document page and text."""

    id: CitationId
    document_id: DocumentId
    document_title: str
    page_number: int
    snippet: str
    tenant_id: str = "default_tenant"
    ticker_symbol: str | None = None


@dataclass(frozen=True)
class Answer:
    """Synthesized factual answer backed by citations and calculations."""

    query_id: QueryId
    text: str
    tenant_id: str = "default_tenant"
    user_id: str | None = None
    citations: list[Citation] = field(default_factory=list)
    reasoning_steps: list[ReasoningStep] = field(default_factory=list)
    confidence_score: float = 1.0
    created_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class EvaluationRun:
    """Quality and correctness benchmark evaluation metrics."""

    id: str = field(default_factory=lambda: str(uuid4()))
    dataset_name: str = ""
    factual_precision: float = 0.0
    retrieval_recall: float = 0.0
    citation_precision: float = 0.0
    numerical_accuracy: float = 0.0
    created_at: datetime = field(default_factory=utc_now)
