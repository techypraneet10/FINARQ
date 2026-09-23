"""Unit tests for Reciprocal Rank Fusion (RRF) candidate blending."""

from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.domain.entities.retrieval import RetrievalCandidate, RetrievalSource
from financial_rag.infrastructure.retrieval.fusion import ReciprocalRankFusion


def test_reciprocal_rank_fusion_blending() -> None:
    fusion = ReciprocalRankFusion(default_k=60)

    chunk_a = DocumentChunk(
        id="chunk-A",
        document_id="doc-1",
        page_number=1,
        chunk_index=0,
        content="Content A",
    )
    chunk_b = DocumentChunk(
        id="chunk-B",
        document_id="doc-1",
        page_number=2,
        chunk_index=1,
        content="Content B",
    )
    chunk_c = DocumentChunk(
        id="chunk-C",
        document_id="doc-2",
        page_number=3,
        chunk_index=0,
        content="Content C",
    )

    # Dense: rank 1 = chunk-A, rank 2 = chunk-B
    dense = [
        RetrievalCandidate(
            chunk=chunk_a,
            dense_score=0.95,
            dense_rank=1,
            sources=[RetrievalSource.DENSE],
        ),
        RetrievalCandidate(
            chunk=chunk_b,
            dense_score=0.85,
            dense_rank=2,
            sources=[RetrievalSource.DENSE],
        ),
    ]

    # Sparse: rank 1 = chunk-B, rank 2 = chunk-C
    sparse = [
        RetrievalCandidate(
            chunk=chunk_b,
            sparse_score=0.90,
            sparse_rank=1,
            sources=[RetrievalSource.SPARSE],
        ),
        RetrievalCandidate(
            chunk=chunk_c,
            sparse_score=0.70,
            sparse_rank=2,
            sources=[RetrievalSource.SPARSE],
        ),
    ]

    fused = fusion.fuse(dense, sparse, rrf_k=60)

    assert len(fused) == 3
    # chunk-B appeared in both (rank 2 in dense + rank 1 in sparse):
    # RRF(B) = (1/62) + (1/61) = 0.016129 + 0.016393 = 0.032522 (highest)
    # RRF(A) = 1/61 = 0.016393
    # RRF(C) = 1/62 = 0.016129
    assert fused[0].chunk.id == "chunk-B"
    assert fused[0].sources == [RetrievalSource.BOTH]
    assert fused[0].dense_score == 0.85
    assert fused[0].sparse_score == 0.90
    assert fused[0].fusion_score == 1.0  # normalized max to 1.0

    assert fused[1].chunk.id == "chunk-A"
    assert fused[1].sources == [RetrievalSource.DENSE]

    assert fused[2].chunk.id == "chunk-C"
    assert fused[2].sources == [RetrievalSource.SPARSE]


def test_reciprocal_rank_fusion_empty() -> None:
    fusion = ReciprocalRankFusion()
    assert fusion.fuse([], []) == []
