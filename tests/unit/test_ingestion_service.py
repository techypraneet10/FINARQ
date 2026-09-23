"""Unit tests for DocumentIngestionService lifecycle and failure recovery."""

import pytest

from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.ingestion.service import DocumentIngestionService
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.common.types import DocumentType, IngestionStatus
from financial_rag.config.settings import (
    ChunkingSettings,
    DatabaseSettings,
    QdrantSettings,
    StorageSettings,
)
from financial_rag.domain.exceptions import DuplicateDocumentError
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


@pytest.fixture
async def ingestion_service(tmp_path):
    # 1. DB
    db_file = tmp_path / "service_test.db"
    db_settings = DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    db_mgr = DatabaseSessionManager(db_settings=db_settings)
    await db_mgr.create_all_tables()

    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)
    ver_repo = PostgresDocumentVersionRepository(session_manager=db_mgr)
    page_repo = PostgresDocumentPageRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)

    # 2. Storage
    storage_settings = StorageSettings(adapter="filesystem", local_dir=str(tmp_path / "storage"))
    storage = FileSystemStorageAdapter(storage_settings=storage_settings)

    # 3. Vector DB
    qdrant_settings = QdrantSettings(collection_name="service_test_col", location=":memory:")
    vector_store = QdrantVectorStoreAdapter(qdrant_settings=qdrant_settings)
    await vector_store.initialize_collection(dimension=64)

    # 4. Pipeline
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

    validator = DocumentValidator()
    service = DocumentIngestionService(
        document_repo=doc_repo,
        version_repo=ver_repo,
        page_repo=page_repo,
        chunk_repo=chunk_repo,
        job_repo=job_repo,
        storage=storage,
        pipeline=pipeline,
        validator=validator,
    )

    yield service
    await db_mgr.close()


@pytest.mark.unit
async def test_service_upload_and_execute_lifecycle(ingestion_service) -> None:
    pdf_bytes = create_sample_10k_pdf()

    # 1. Upload & Register
    doc, version, job = await ingestion_service.upload_and_register_document(
        content=pdf_bytes,
        filename="apple_10k.pdf",
        document_type=DocumentType.SEC_10K,
        title="Apple Inc. 10-K FY2023",
        ticker_symbol="AAPL",
        fiscal_year=2023,
        fiscal_period="FY",
    )

    assert doc.title == "Apple Inc. 10-K FY2023"
    assert doc.ticker_symbol == "AAPL"
    assert version.version_number == 1
    assert job.status == IngestionStatus.PENDING

    # 2. Execute Ingestion Job
    completed_job = await ingestion_service.execute_ingestion_job(job.id)
    assert completed_job.status == IngestionStatus.COMPLETED
    assert completed_job.progress_pct == 100.0
    assert completed_job.chunks_indexed > 0

    # 3. Verify Persisted Pages and Chunks
    pages = await ingestion_service.get_document(doc.id)
    assert pages is not None
    assert pages.pages_count == 3

    chunks = await ingestion_service.get_document_chunks(doc.id)
    assert len(chunks) == completed_job.chunks_indexed
    for c in chunks:
        assert c.document_id == doc.id
        assert c.document_version_id == version.id


@pytest.mark.unit
async def test_service_duplicate_detection(ingestion_service) -> None:
    pdf_bytes = create_sample_10k_pdf()

    # First upload
    await ingestion_service.upload_and_register_document(
        content=pdf_bytes,
        filename="first_upload.pdf",
        document_type=DocumentType.SEC_10K,
    )

    # Second upload with identical bytes must raise DuplicateDocumentError
    with pytest.raises(DuplicateDocumentError, match="identical binary hash already exists"):
        await ingestion_service.upload_and_register_document(
            content=pdf_bytes,
            filename="second_upload.pdf",
            document_type=DocumentType.SEC_10K,
        )


@pytest.mark.unit
async def test_service_retry_job(ingestion_service) -> None:
    pdf_bytes = create_sample_10k_pdf()
    _doc, _version, job = await ingestion_service.upload_and_register_document(
        content=pdf_bytes,
        filename="retry_test.pdf",
    )

    # Execute
    retried_job = await ingestion_service.retry_ingestion_job(job.id)
    assert retried_job.status == IngestionStatus.COMPLETED
