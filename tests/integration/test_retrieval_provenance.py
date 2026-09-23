"""Aggressive integration tests proving complete provenance preservation across all retrieval stages."""

import pytest

from financial_rag.application.retrieval.service import RetrievalService
from financial_rag.common.types import ChunkType
from financial_rag.config.settings import QdrantSettings
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.retrieval import (
    BM25SparseRetriever,
    CandidateDeduplicator,
    EvidenceSelector,
    EvidenceValidator,
    FinancialQueryAnalyzer,
    MockReranker,
    QdrantDenseRetriever,
    ReciprocalRankFusion,
)
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter


@pytest.mark.asyncio
async def test_provenance_preservation_across_all_stages() -> None:
    """Prove that every provenance field remains intact from raw chunk to final EvidenceSet."""

    # 1. Create a rich DocumentChunk with full metadata and provenance
    original_chunk = DocumentChunk(
        id="chunk-prov-001",
        document_id="doc-prov-abc",
        document_version_id="ver-prov-v2",
        page_number=42,
        page_numbers=[42, 43],
        chunk_index=7,
        chunk_type=ChunkType.TABLE,
        content="| Operating Margin | 31.5% |\n| Net Income | $93,736M |",
        source_block_ids=["block-1", "block-2"],
        section_path="PART II > Item 8. Financial Statements > Note 12. Segment Reporting",
        table_id="table-seg-12",
        metadata={
            "ticker_symbol": "AAPL",
            "fiscal_year": 2024,
            "fiscal_period": "FY",
            "bounding_box": {"x0": 50.0, "y0": 100.0, "x1": 550.0, "y1": 400.0},
        },
    )

    # 2. Setup Dense and Sparse storage
    embedder = MockEmbeddingProvider(dimension=1536)
    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(location=":memory:", collection_name="prov_financial_chunks")
    )
    embeddings = await embedder.embed_batch([original_chunk.content])
    await vector_store.upsert_chunks(chunks=[original_chunk], embeddings=embeddings)

    sparse_retriever = BM25SparseRetriever()
    await sparse_retriever.index_chunks([original_chunk])

    # 3. Dense Retrieval Stage verification
    dense_retriever = QdrantDenseRetriever(
        embedding_provider=embedder, vector_store=vector_store, expected_dimension=1536
    )
    analyzer = FinancialQueryAnalyzer()
    query = analyzer.analyze("What was operating margin in 2024?")

    dense_candidates = await dense_retriever.retrieve(query)
    assert len(dense_candidates) == 1
    d_cand = dense_candidates[0]
    assert d_cand.provenance is not None
    assert d_cand.provenance.document_id == "doc-prov-abc"
    assert d_cand.provenance.document_version_id == "ver-prov-v2"
    assert d_cand.provenance.page_numbers == [42, 43]
    assert d_cand.provenance.source_block_ids == ["block-1", "block-2"]
    assert (
        d_cand.provenance.section_path
        == "PART II > Item 8. Financial Statements > Note 12. Segment Reporting"
    )
    assert d_cand.provenance.table_id == "table-seg-12"
    assert d_cand.provenance.chunk_id == "chunk-prov-001"

    # 4. Sparse Retrieval Stage verification
    sparse_candidates = await sparse_retriever.retrieve(query)
    assert len(sparse_candidates) == 1
    s_cand = sparse_candidates[0]
    assert s_cand.provenance is not None
    assert s_cand.provenance.document_id == "doc-prov-abc"
    assert s_cand.provenance.chunk_id == "chunk-prov-001"

    # 5. Fusion Stage verification
    fusion = ReciprocalRankFusion(default_k=60)
    fused = fusion.fuse(dense_candidates, sparse_candidates)
    assert len(fused) == 1
    f_cand = fused[0]
    assert f_cand.provenance is not None
    assert f_cand.provenance.document_id == "doc-prov-abc"
    assert f_cand.provenance.document_version_id == "ver-prov-v2"
    assert f_cand.dense_score is not None
    assert f_cand.sparse_score is not None
    assert f_cand.fusion_score is not None

    # 6. Deduplication Stage verification
    deduplicator = CandidateDeduplicator()
    deduped = deduplicator.deduplicate(fused)
    assert len(deduped) == 1
    assert deduped[0].provenance is not None
    assert deduped[0].provenance.document_id == "doc-prov-abc"

    # 7. Reranking Stage verification
    reranker = MockReranker()
    reranked = await reranker.rerank(query, deduped)
    assert len(reranked) == 1
    assert reranked[0].provenance is not None
    assert reranked[0].provenance.document_id == "doc-prov-abc"
    assert reranked[0].reranker_score is not None

    # 8. Selection Stage verification
    selector = EvidenceSelector()
    selected = selector.select(query, reranked, top_k=1)
    assert len(selected) == 1
    sel_item = selected[0]
    assert sel_item.chunk_id == "chunk-prov-001"
    assert sel_item.document_id == "doc-prov-abc"
    assert sel_item.document_version_id == "ver-prov-v2"
    assert sel_item.page_number == 42
    assert sel_item.page_numbers == [42, 43]
    assert sel_item.chunk_type == ChunkType.TABLE
    assert (
        sel_item.section_path
        == "PART II > Item 8. Financial Statements > Note 12. Segment Reporting"
    )
    assert sel_item.table_id == "table-seg-12"
    assert sel_item.source_block_ids == ["block-1", "block-2"]
    assert sel_item.bounding_box == {"x0": 50.0, "y0": 100.0, "x1": 550.0, "y1": 400.0}
    assert sel_item.ticker == "AAPL"
    assert sel_item.fiscal_year == 2024
    assert sel_item.fiscal_period == "FY"

    # 9. End-to-End Service execution verification
    service = RetrievalService(
        query_analyzer=analyzer,
        dense_retriever=dense_retriever,
        sparse_retriever=sparse_retriever,
        fusion_strategy=fusion,
        deduplicator=deduplicator,
        reranker=reranker,
        evidence_selector=selector,
        evidence_validator=EvidenceValidator(),
    )

    evidence_set = await service.search("What was operating margin?", top_k=1)
    assert evidence_set.evidence_count == 1
    final_evidence = evidence_set.items[0]

    # Verify every single required provenance attribute on final output
    assert final_evidence.chunk_id == "chunk-prov-001"
    assert final_evidence.document_id == "doc-prov-abc"
    assert final_evidence.document_version_id == "ver-prov-v2"
    assert final_evidence.page_numbers == [42, 43]
    assert final_evidence.chunk_type == ChunkType.TABLE
    assert (
        final_evidence.section_path
        == "PART II > Item 8. Financial Statements > Note 12. Segment Reporting"
    )
    assert final_evidence.table_id == "table-seg-12"
    assert final_evidence.source_block_ids == ["block-1", "block-2"]
    assert final_evidence.content_hash != ""
    assert final_evidence.ticker == "AAPL"
    assert final_evidence.fiscal_year == 2024
    assert final_evidence.dense_score is not None
    assert final_evidence.sparse_score is not None
    assert final_evidence.fusion_score is not None
    assert final_evidence.reranker_score is not None
    assert final_evidence.final_score > 0.0
