"""Domain entities and value objects for retrieval, ranking, and evidence selection.

These models encapsulate core retrieval business concepts, maintaining complete
provenance and score breakdowns across dense, sparse, fusion, and reranking stages.
They are strictly independent of databases, web frameworks, vector stores, and external APIs.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from financial_rag.common.types import (
    BlockId,
    ChunkId,
    ChunkType,
    DocumentId,
    PageId,
    QueryId,
    TableId,
    VersionId,
)
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.value_objects import ProvenanceLineage


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


class QueryType(StrEnum):
    """Categorical classification of user financial inquiries."""

    FACTUAL = "factual"
    COMPARISON = "comparison"
    TREND = "trend"
    DEFINITION = "definition"
    NUMERICAL = "numerical"
    TABLE_LOOKUP = "table_lookup"
    SECTION_SPECIFIC = "section_specific"
    DOCUMENT_SPECIFIC = "document_specific"
    MULTI_DOCUMENT = "multi_document"
    UNKNOWN = "unknown"


class RetrievalSource(StrEnum):
    """Identifies the retrieval system(s) that produced a candidate chunk."""

    DENSE = "dense"
    SPARSE = "sparse"
    BOTH = "both"


@dataclass(frozen=True)
class FinancialSignals:
    """High-confidence structural and financial metadata extracted from query text."""

    tickers: list[str] = field(default_factory=list)
    company_names: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    fiscal_years: list[int] = field(default_factory=list)
    fiscal_periods: list[str] = field(default_factory=list)  # e.g., ["Q1", "Q3", "FY"]
    sections: list[str] = field(default_factory=list)  # e.g., ["Item 1A", "Item 7", "MD&A"]
    statement_types: list[str] = field(
        default_factory=list
    )  # e.g., ["Balance Sheet", "Income Statement"]
    currencies: list[str] = field(default_factory=list)  # e.g., ["USD", "EUR"]
    is_comparison: bool = False
    is_table_lookup: bool = False
    is_multi_period: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert signals to dictionary representation."""
        return {
            "tickers": self.tickers,
            "company_names": self.company_names,
            "metrics": self.metrics,
            "fiscal_years": self.fiscal_years,
            "fiscal_periods": self.fiscal_periods,
            "sections": self.sections,
            "statement_types": self.statement_types,
            "currencies": self.currencies,
            "is_comparison": self.is_comparison,
            "is_table_lookup": self.is_table_lookup,
            "is_multi_period": self.is_multi_period,
        }


@dataclass(frozen=True)
class RetrievalFilter:
    """Domain-level filtering criteria applied across retrieval stages."""

    document_ids: list[DocumentId] | None = None
    version_ids: list[VersionId] | None = None
    tenant_id: str | None = None
    ticker_symbols: list[str] | None = None
    fiscal_years: list[int] | None = None
    fiscal_periods: list[str] | None = None
    document_types: list[str] | None = None
    sections: list[str] | None = None
    chunk_types: list[str] | None = None
    table_only: bool | None = None
    custom_metadata: dict[str, Any] = field(default_factory=dict)

    def is_empty(self) -> bool:
        """Check whether any filter conditions are set."""
        return (
            self.document_ids is None
            and self.version_ids is None
            and self.tenant_id is None
            and self.ticker_symbols is None
            and self.fiscal_years is None
            and self.fiscal_periods is None
            and self.document_types is None
            and self.sections is None
            and self.chunk_types is None
            and self.table_only is None
            and not self.custom_metadata
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert filter criteria to dictionary representation."""
        return {
            "document_ids": [str(d) for d in self.document_ids] if self.document_ids else None,
            "version_ids": [str(v) for v in self.version_ids] if self.version_ids else None,
            "tenant_id": self.tenant_id,
            "ticker_symbols": self.ticker_symbols,
            "fiscal_years": self.fiscal_years,
            "fiscal_periods": self.fiscal_periods,
            "document_types": self.document_types,
            "sections": self.sections,
            "chunk_types": self.chunk_types,
            "table_only": self.table_only,
            "custom_metadata": self.custom_metadata,
        }


@dataclass(frozen=True)
class RetrievalQuery:
    """Formalized retrieval inquiry containing analyzed intent and financial parameters."""

    raw_query: str
    normalized_query: str
    tenant_id: str = "default_tenant"
    query_type: QueryType = QueryType.UNKNOWN
    signals: FinancialSignals = field(default_factory=FinancialSignals)
    filters: RetrievalFilter = field(default_factory=RetrievalFilter)
    top_k: int = 10
    dense_top_k: int = 50
    sparse_top_k: int = 50
    rerank_top_k: int = 20
    id: QueryId = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=utc_now)


@dataclass
class RetrievalCandidate:
    """Intermediate candidate chunk during fusion, deduplication, and reranking."""

    chunk: DocumentChunk
    dense_score: float | None = None
    sparse_score: float | None = None
    dense_rank: int | None = None
    sparse_rank: int | None = None
    fusion_score: float = 0.0
    reranker_score: float | None = None
    final_score: float = 0.0
    sources: list[RetrievalSource] = field(default_factory=list)
    provenance: ProvenanceLineage | None = None

    def __post_init__(self) -> None:
        """Derive provenance if not explicitly provided."""
        if self.provenance is None:
            self.provenance = self.chunk.get_provenance()
        if not self.sources:
            if self.dense_score is not None and self.sparse_score is not None:
                self.sources = [RetrievalSource.BOTH]
            elif self.dense_score is not None:
                self.sources = [RetrievalSource.DENSE]
            elif self.sparse_score is not None:
                self.sources = [RetrievalSource.SPARSE]


@dataclass(frozen=True)
class RankedEvidence:
    """Final, validated evidence unit with complete provenance and score transparency."""

    rank: int
    chunk_id: ChunkId
    document_id: DocumentId
    document_version_id: VersionId
    page_number: int
    page_numbers: list[int]
    chunk_type: ChunkType
    content: str
    section_path: str
    table_id: TableId | None
    source_block_ids: list[BlockId]
    bounding_box: dict[str, float] | None
    content_hash: str
    ticker: str | None
    fiscal_year: int | None
    fiscal_period: str | None
    retrieval_sources: list[RetrievalSource]
    dense_score: float | None
    sparse_score: float | None
    fusion_score: float
    reranker_score: float | None
    final_score: float
    provenance: ProvenanceLineage
    tenant_id: str = "default_tenant"
    page_id: PageId | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence item to serializable dictionary."""
        return {
            "rank": self.rank,
            "chunk_id": str(self.chunk_id),
            "document_id": str(self.document_id),
            "document_version_id": str(self.document_version_id),
            "page_number": self.page_number,
            "page_numbers": self.page_numbers,
            "chunk_type": self.chunk_type.value,
            "content": self.content,
            "section_path": self.section_path,
            "table_id": str(self.table_id) if self.table_id else None,
            "source_block_ids": [str(bid) for bid in self.source_block_ids],
            "bounding_box": self.bounding_box,
            "content_hash": self.content_hash,
            "ticker": self.ticker,
            "fiscal_year": self.fiscal_year,
            "fiscal_period": self.fiscal_period,
            "retrieval_sources": [s.value for s in self.retrieval_sources],
            "dense_score": self.dense_score,
            "sparse_score": self.sparse_score,
            "fusion_score": self.fusion_score,
            "reranker_score": self.reranker_score,
            "final_score": self.final_score,
            "provenance": self.provenance.to_dict(),
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EvidenceSet:
    """Ranked, deduplicated, provenance-preserving evidence set answering a retrieval query."""

    query_id: QueryId
    query: RetrievalQuery
    items: list[RankedEvidence]
    total_candidates: int
    retrieval_strategy: str
    execution_stages: list[str]
    timing_ms: dict[str, float]
    fallback_occurred: bool = False
    fallback_reason: str | None = None
    created_at: datetime = field(default_factory=utc_now)

    @property
    def evidence_count(self) -> int:
        """Number of ranked evidence items."""
        return len(self.items)

    def to_dict(self) -> dict[str, Any]:
        """Convert evidence set to serializable response dictionary."""
        return {
            "query_id": str(self.query_id),
            "raw_query": self.query.raw_query,
            "normalized_query": self.query.normalized_query,
            "query_type": self.query.query_type.value,
            "signals": self.query.signals.to_dict(),
            "retrieval_strategy": self.retrieval_strategy,
            "execution_stages": self.execution_stages,
            "evidence_count": self.evidence_count,
            "total_candidates": self.total_candidates,
            "fallback_occurred": self.fallback_occurred,
            "fallback_reason": self.fallback_reason,
            "evidence": [item.to_dict() for item in self.items],
            "timing_ms": self.timing_ms,
            "created_at": self.created_at.isoformat(),
        }
