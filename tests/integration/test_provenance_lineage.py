"""Integration test verifying strict end-to-end lineage invariant:
Vector Payload -> Chunk -> Block / Table -> Page -> Version -> Document.
"""

import pytest

from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.ingestion.service import DocumentIngestionService
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.common.types import DocumentType
from financial_rag.config.settings import (
    ChunkingSettings,
    DatabaseSettings,
    QdrantSettings,
    StorageSettings,
)
from financial_rag.infrastructure.chunking.structure_aware import StructureAwareChunker
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.normalization.document_normalizer import DocumentNormalizer
from financial_rag.infrastructure.parsing.pdf_parser import PyMuPDFParser
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresDocumentChunkRepository,
    PostgresDocumentPageRepository,
    PostgresDocumentRepository,
    PostgresDocumentVersionRepository,
    PostgresIngestionJobRepository,
)
from financial_rag.infrastructure.storage.filesystem import FileSystemStorageAdapter
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector
from financial_rag.infrastructure.table.extractor import FinancialTableExtractor
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.mark.integration
async def test_strict_provenance_lineage_invariant(tmp_path) -> None:
    """Validate that every vector indexed point resolves through the complete lineage graph:
    Vector Point Payload -> DocumentChunk -> LayoutBlock / Table -> DocumentPage -> DocumentVersion -> Document.
    """
    # 1. Setup SQLite Persistence
    db_file = tmp_path / "lineage_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)
    ver_repo = PostgresDocumentVersionRepository(session_manager=db_mgr)
    page_repo = PostgresDocumentPageRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)

    # 2. Storage & Vector DB
    storage = FileSystemStorageAdapter(
        storage_settings=StorageSettings(adapter="filesystem", local_dir=str(tmp_path / "storage"))
    )
    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(collection_name="lineage_col", location=":memory:")
    )
    await vector_store.initialize_collection(dimension=64)

    embedder = MockEmbeddingProvider(dimension=64)
    table_normalizer = FinancialTableNormalizer()
    table_extractor = FinancialTableExtractor(normalizer=table_normalizer)
    pipeline = IngestionPipeline(
        parser=PyMuPDFParser(),
        table_extractor=table_extractor,
        table_normalizer=table_normalizer,
        normalizer=DocumentNormalizer(),
        structure_detector=FinancialStructureDetector(),
        chunker=StructureAwareChunker(chunking_settings=ChunkingSettings()),
        embedding_provider=embedder,
        vector_store=vector_store,
    )

    service = DocumentIngestionService(
        document_repo=doc_repo,
        version_repo=ver_repo,
        page_repo=page_repo,
        chunk_repo=chunk_repo,
        job_repo=job_repo,
        storage=storage,
        pipeline=pipeline,
        validator=DocumentValidator(),
    )

    # 3. Ingest Document
    pdf_bytes = create_sample_10k_pdf()
    doc, version, job = await service.upload_and_register_document(
        content=pdf_bytes,
        filename="ACME_10K_FY2023.pdf",
        document_type=DocumentType.SEC_10K,
        ticker_symbol="ACME",
        fiscal_year=2023,
        fiscal_period="FY",
    )

    await service.execute_ingestion_job(job.id)

    # 4. Search and retrieve vector points
    query_vec = await embedder.embed_text("balance sheet cash and cash equivalents")
    retrieval_results = await vector_store.search(query_vector=query_vec, top_k=10)

    assert len(retrieval_results) > 0

    # 5. Verify Lineage Invariant for EVERY retrieved vector point
    for result in retrieval_results:
        chunk = result.chunk

        # [Lineage Step 1]: Vector Point -> Chunk Record
        assert chunk.id is not None
        assert chunk.document_id == doc.id
        assert chunk.document_version_id == version.id
        assert chunk.page_number in [1, 2, 3]

        # Verify Chunk in Relational Store
        db_chunks = await chunk_repo.get_by_document_id(doc.id)
        matching_db_chunk = next((c for c in db_chunks if str(c.id) == str(chunk.id)), None)
        assert matching_db_chunk is not None, f"Chunk {chunk.id} not found in relational store"

        # [Lineage Step 2]: Chunk -> Page Record
        pages = await page_repo.get_by_version_id(version.id)
        matching_page = next((p for p in pages if p.page_number == chunk.page_number), None)
        assert matching_page is not None, (
            f"Page {chunk.page_number} not found for version {version.id}"
        )
        assert matching_page.document_id == doc.id
        assert matching_page.version_id == version.id

        # [Lineage Step 3]: Chunk -> Source Blocks / Tables on Page
        if chunk.source_block_ids:
            page_block_ids = {str(b.id) for b in matching_page.blocks}
            for s_id in chunk.source_block_ids:
                assert str(s_id) in page_block_ids, (
                    f"Source block {s_id} missing on Page {matching_page.page_number}"
                )

        if chunk.table_id:
            page_table_ids = {str(t.id) for t in matching_page.tables}
            assert str(chunk.table_id) in page_table_ids, (
                f"Table {chunk.table_id} missing on Page {matching_page.page_number}"
            )

        # [Lineage Step 4]: Page -> DocumentVersion Record
        db_version = await ver_repo.get_by_id(version.id)
        assert db_version is not None
        assert db_version.id == version.id
        assert db_version.document_id == doc.id

        # [Lineage Step 5]: DocumentVersion -> Parent Document Record
        db_doc = await doc_repo.get_by_id(doc.id)
        assert db_doc is not None
        assert db_doc.id == doc.id
        assert db_doc.current_version_id == version.id
        assert db_doc.ticker_symbol == "ACME"

    await db_mgr.close()
