"""Unit tests for candidate deduplicator."""

from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import RetrievalCandidate, RetrievalSource
from financial_rag.infrastructure.retrieval.deduplicator import CandidateDeduplicator


def test_candidate_deduplicator_merging() -> None:
    deduplicator = CandidateDeduplicator()

    chunk = DocumentChunk(
        id="chunk-dup",
        document_id="doc-1",
        document_version_id="ver-1",
        page_number=1,
        chunk_index=0,
        content="Duplicate chunk text",
    )

    cands = [
        RetrievalCandidate(
            chunk=chunk,
            dense_score=0.88,
            dense_rank=1,
            fusion_score=0.8,
            final_score=0.8,
            sources=[RetrievalSource.DENSE],
        ),
        RetrievalCandidate(
            chunk=chunk,
            sparse_score=0.92,
            sparse_rank=2,
            fusion_score=0.7,
            final_score=0.7,
            sources=[RetrievalSource.SPARSE],
        ),
    ]

    deduped = deduplicator.deduplicate(cands)
    assert len(deduped) == 1
    result = deduped[0]
    assert result.chunk.id == "chunk-dup"
    assert result.sources == [RetrievalSource.BOTH]
    assert result.dense_score == 0.88
    assert result.sparse_score == 0.92
    assert result.final_score == 0.8


def test_deduplicator_empty() -> None:
    deduplicator = CandidateDeduplicator()
    assert deduplicator.deduplicate([]) == []
