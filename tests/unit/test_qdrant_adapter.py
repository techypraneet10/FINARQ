"""Unit tests for QdrantVectorStoreAdapter using in-memory local storage."""

import pytest

from financial_rag.common.types import ChunkType
from financial_rag.config.settings import QdrantSettings
from financial_rag.domain.entities.models import DocumentChunk
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter


@pytest.fixture
async def qdrant_adapter():
    settings = QdrantSettings(collection_name="test_financial_chunks", location=":memory:")
    adapter = QdrantVectorStoreAdapter(qdrant_settings=settings)
    await adapter.initialize_collection(dimension=64)
    yield adapter


@pytest.mark.unit
async def test_qdrant_adapter_upsert_search_and_provenance(qdrant_adapter) -> None:
    embedder = MockEmbeddingProvider(dimension=64)

    chunk1 = DocumentChunk(
        id="c1111111-1111-1111-1111-111111111111",
        document_id="doc-aapl",
        document_version_id="ver-1",
        page_number=15,
        page_numbers=[15],
        chunk_index=0,
        chunk_type=ChunkType.TEXT,
        content="Apple reported total revenue of $383,285 million in fiscal year 2023.",
        section_path="Part I > Item 1. Business",
        token_count=18,
        char_count=65,
        metadata={"ticker": "AAPL"},
    )

    chunk2 = DocumentChunk(
        id="c2222222-2222-2222-2222-222222222222",
        document_id="doc-msft",
        document_version_id="ver-1",
        page_number=20,
        page_numbers=[20],
        chunk_index=1,
        chunk_type=ChunkType.TABLE,
        content="| Segment | Revenue |\n| Intelligent Cloud | $87,907 |",
        section_path="Part II > Item 8. Financial Statements",
        table_id="tbl-msft-01",
        token_count=20,
        char_count=55,
        metadata={"ticker": "MSFT"},
    )

    chunks = [chunk1, chunk2]
    vectors = await embedder.embed_batch([c.content for c in chunks])

    # 1. Upsert Chunks
    upsert_ok = await qdrant_adapter.upsert_chunks(chunks=chunks, embeddings=vectors)
    assert upsert_ok is True

    # 2. Search
    query_vec = await embedder.embed_text("Apple fiscal year 2023 revenue")
    results = await qdrant_adapter.search(query_vector=query_vec, top_k=2)

    assert len(results) > 0
    top_chunk = results[0].chunk
    assert top_chunk.document_id in ["doc-aapl", "doc-msft"]

    # Check that provenance fields are retained in the payload
    if top_chunk.document_id == "doc-aapl":
        assert top_chunk.section_path == "Part I > Item 1. Business"
        assert top_chunk.page_number == 15
        assert top_chunk.document_version_id == "ver-1"

    # 3. Delete by Document ID
    del_ok = await qdrant_adapter.delete_by_document_id("doc-aapl")
    assert del_ok is True

    # 4. Search again - doc-aapl should be gone
    res_after_del = await qdrant_adapter.search(query_vector=query_vec, top_k=5)
    remaining_doc_ids = [r.chunk.document_id for r in res_after_del]
    assert "doc-aapl" not in remaining_doc_ids
