"""Domain interfaces (architectural protocols) for retrieval, ranking, and evidence selection.

These contracts ensure that dense retrieval, sparse BM25, reciprocal rank fusion,
cross-encoder reranking, evidence selection, and quality validation are completely
decoupled from concrete infrastructure implementations.
"""

from typing import Protocol, runtime_checkable

from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import (
    EvidenceSet,
    RankedEvidence,
    RetrievalCandidate,
    RetrievalFilter,
    RetrievalQuery,
)


@runtime_checkable
class QueryAnalyzerProtocol(Protocol):
    """Contract for query normalization, classification, and financial signals extraction."""

    def analyze(
        self,
        raw_query: str,
        filters: RetrievalFilter | None = None,
        top_k: int = 10,
        dense_top_k: int = 50,
        sparse_top_k: int = 50,
        rerank_top_k: int = 20,
    ) -> RetrievalQuery:
        """Analyze, normalize, classify, and extract structured signals from raw user query."""
        ...


@runtime_checkable
class DenseRetrieverProtocol(Protocol):
    """Contract for dense vector retrieval over vector indices (e.g. Qdrant)."""

    async def retrieve(
        self,
        query: RetrievalQuery,
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Execute semantic vector search against indexed embeddings."""
        ...

    async def health_check(self) -> bool:
        """Verify vector index availability and model compatibility."""
        ...


@runtime_checkable
class SparseRetrieverProtocol(Protocol):
    """Contract for sparse lexical retrieval (e.g. BM25 inverted index)."""

    async def retrieve(
        self,
        query: RetrievalQuery,
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Execute BM25 keyword search with exact financial term boosting."""
        ...

    async def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Index or update document chunks into the sparse lexical search engine."""
        ...

    async def delete_by_document_id(self, document_id: str) -> bool:
        """Remove indexed document chunks from the sparse index."""
        ...

    async def health_check(self) -> bool:
        """Verify sparse index health."""
        ...


@runtime_checkable
class FusionStrategyProtocol(Protocol):
    """Contract for multi-retriever candidate pool fusion (e.g. Reciprocal Rank Fusion)."""

    def fuse(
        self,
        dense_candidates: list[RetrievalCandidate],
        sparse_candidates: list[RetrievalCandidate],
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
    ) -> list[RetrievalCandidate]:
        """Fuse and rank candidate sets, preserving provenance and individual score breakdowns."""
        ...


@runtime_checkable
class CandidateDeduplicatorProtocol(Protocol):
    """Contract for deduplicating candidate chunks across multi-retrieval streams."""

    def deduplicate(
        self,
        candidates: list[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:
        """Deduplicate candidate pool by unique chunk identity while merging scores and lineage."""
        ...


@runtime_checkable
class RerankerProtocol(Protocol):
    """Contract for cross-encoder reranking over a bounded candidate set."""

    async def rerank(
        self,
        query: RetrievalQuery,
        candidates: list[RetrievalCandidate],
        top_k: int | None = None,
    ) -> list[RetrievalCandidate]:
        """Score query-candidate pairs with cross-encoder and return reranked list."""
        ...

    async def health_check(self) -> bool:
        """Verify reranker model availability."""
        ...


@runtime_checkable
class EvidenceSelectorProtocol(Protocol):
    """Contract for balancing relevance, diversity, and financial structure preservation."""

    def select(
        self,
        query: RetrievalQuery,
        candidates: list[RetrievalCandidate],
        top_k: int = 10,
        diversity_threshold: float = 0.8,
        max_chunks_per_document: int = 5,
    ) -> list[RankedEvidence]:
        """Select top evidence respecting document diversity, page coverage, and table retention."""
        ...


@runtime_checkable
class EvidenceValidatorProtocol(Protocol):
    """Contract for quality guardrails and rejection of corrupted/incomplete evidence."""

    def validate_and_sanitize(
        self,
        evidence_items: list[RankedEvidence],
    ) -> list[RankedEvidence]:
        """Validate presence of complete provenance, non-empty text, and well-formed metadata."""
        ...


@runtime_checkable
class RetrievalServiceProtocol(Protocol):
    """Contract for end-to-end retrieval application service."""

    async def search(
        self,
        raw_query: str,
        filters: RetrievalFilter | None = None,
        top_k: int = 10,
        dense_top_k: int | None = None,
        sparse_top_k: int | None = None,
        rerank_top_k: int | None = None,
        use_reranker: bool = True,
    ) -> EvidenceSet:
        """Execute full hybrid retrieval, fusion, reranking, and evidence selection pipeline."""
        ...
