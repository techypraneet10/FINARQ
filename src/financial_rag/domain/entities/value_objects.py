"""Domain value objects for layout, provenance, and financial structures."""

from dataclasses import dataclass, field
from typing import Any

from financial_rag.common.types import BlockId, ChunkId, DocumentId, TableId, VersionId


@dataclass(frozen=True)
class BoundingBox:
    """Normalized or absolute coordinate bounding box on a document page."""

    x0: float
    y0: float
    x1: float
    y1: float
    page_width: float = 0.0
    page_height: float = 0.0

    @property
    def width(self) -> float:
        """Calculate width of bounding box."""
        return max(0.0, self.x1 - self.x0)

    @property
    def height(self) -> float:
        """Calculate height of bounding box."""
        return max(0.0, self.y1 - self.y0)

    @property
    def area(self) -> float:
        """Calculate bounding box area."""
        return self.width * self.height

    def to_dict(self) -> dict[str, float]:
        """Convert to dictionary representation."""
        return {
            "x0": self.x0,
            "y0": self.y0,
            "x1": self.x1,
            "y1": self.y1,
            "page_width": self.page_width,
            "page_height": self.page_height,
        }


@dataclass(frozen=True)
class TableCell:
    """A single cell inside an extracted financial table."""

    row_index: int
    col_index: int
    text: str
    row_span: int = 1
    col_span: int = 1
    numeric_value: float | None = None
    is_header: bool = False
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert cell to dictionary."""
        return {
            "row_index": self.row_index,
            "col_index": self.col_index,
            "text": self.text,
            "row_span": self.row_span,
            "col_span": self.col_span,
            "numeric_value": self.numeric_value,
            "is_header": self.is_header,
        }


@dataclass(frozen=True)
class SectionHeader:
    """Detected structural heading or SEC item."""

    title: str
    level: int = 1
    item_code: str | None = None  # e.g., "Item 1A", "Item 7", "Item 8"
    path: str = ""  # e.g., "PART I > Item 1A. Risk Factors"


@dataclass(frozen=True)
class ProvenanceLineage:
    """Full lineage tracing a chunk or vector record back to its source."""

    document_id: DocumentId
    document_version_id: VersionId
    page_numbers: list[int]
    source_block_ids: list[BlockId] = field(default_factory=list)
    section_path: str = ""
    chunk_type: str = "text"
    table_id: TableId | None = None
    chunk_id: ChunkId | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert lineage to payload dictionary."""
        return {
            "document_id": str(self.document_id),
            "document_version_id": str(self.document_version_id),
            "page_numbers": self.page_numbers,
            "source_block_ids": [str(bid) for bid in self.source_block_ids],
            "section_path": self.section_path,
            "chunk_type": self.chunk_type,
            "table_id": str(self.table_id) if self.table_id else None,
            "chunk_id": str(self.chunk_id) if self.chunk_id else None,
        }
