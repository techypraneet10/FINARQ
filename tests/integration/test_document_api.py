"""Integration tests for Document Ingestion and Management REST APIs."""

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.api.dependencies import (
    get_chunk_repository,
    get_db_session_manager,
    get_document_repository,
    get_ingestion_job_repository,
    get_ingestion_service,
    get_page_repository,
    get_version_repository,
)
from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.ingestion.service import DocumentIngestionService
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.config.settings import (
    ChunkingSettings,
    DatabaseSettings,
    QdrantSettings,
    SecuritySettings,
    Settings,
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
from financial_rag.main import create_app
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.fixture
async def api_client(tmp_path):
    # Setup test test DB
    db_file = tmp_path / "api_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    test_app = create_app(settings=Settings(security=SecuritySettings(auth_disabled_dev=True)))

    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)
    ver_repo = PostgresDocumentVersionRepository(session_manager=db_mgr)
    page_repo = PostgresDocumentPageRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)

    storage = FileSystemStorageAdapter(
        storage_settings=StorageSettings(
            adapter="filesystem", local_dir=str(tmp_path / "api_storage")
        )
    )
    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(collection_name="api_test_col", location=":memory:")
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

    test_service = DocumentIngestionService(
        document_repo=doc_repo,
        version_repo=ver_repo,
        page_repo=page_repo,
        chunk_repo=chunk_repo,
        job_repo=job_repo,
        storage=storage,
        pipeline=pipeline,
        validator=DocumentValidator(),
    )

    test_app.dependency_overrides[get_ingestion_service] = lambda: test_service
    test_app.dependency_overrides[get_document_repository] = lambda: doc_repo
    test_app.dependency_overrides[get_version_repository] = lambda: ver_repo
    test_app.dependency_overrides[get_page_repository] = lambda: page_repo
    test_app.dependency_overrides[get_chunk_repository] = lambda: chunk_repo
    test_app.dependency_overrides[get_ingestion_job_repository] = lambda: job_repo
    test_app.dependency_overrides[get_db_session_manager] = lambda: db_mgr

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    test_app.dependency_overrides.clear()
    await db_mgr.close()


@pytest.mark.integration
async def test_document_upload_and_query_api_flow(api_client) -> None:
    pdf_bytes = create_sample_10k_pdf()

    # 1. Upload Document
    files = {"file": ("apple_10k.pdf", pdf_bytes, "application/pdf")}
    data = {
        "document_type": "10-K",
        "title": "Apple Inc. 10-K FY2023",
        "ticker_symbol": "AAPL",
        "fiscal_year": 2023,
        "fiscal_period": "FY",
    }
    upload_resp = await api_client.post("/api/v1/documents", files=files, data=data)
    assert upload_resp.status_code == 202
    upload_json = upload_resp.json()
    assert "document_id" in upload_json
    assert "version_id" in upload_json
    assert "job_id" in upload_json
    assert upload_json["title"] == "Apple Inc. 10-K FY2023"

    doc_id = upload_json["document_id"]
    job_id = upload_json["job_id"]

    # 2. Check Job Status
    job_resp = await api_client.get(f"/api/v1/ingestion-jobs/{job_id}")
    assert job_resp.status_code == 200
    job_json = job_resp.json()
    assert job_json["document_id"] == doc_id
    assert job_json["status"] in ["pending", "processing", "completed"]

    # 3. List Documents
    list_resp = await api_client.get("/api/v1/documents?ticker_symbol=AAPL")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id
    assert docs[0]["ticker_symbol"] == "AAPL"

    # 4. Get Document Details
    detail_resp = await api_client.get(f"/api/v1/documents/{doc_id}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["title"] == "Apple Inc. 10-K FY2023"

    # 5. Get Document Versions
    vers_resp = await api_client.get(f"/api/v1/documents/{doc_id}/versions")
    assert vers_resp.status_code == 200
    versions = vers_resp.json()
    assert len(versions) == 1
    assert versions[0]["version_number"] == 1

    # 6. Retry Ingestion Job
    retry_resp = await api_client.post(f"/api/v1/ingestion-jobs/{job_id}/retry")
    assert retry_resp.status_code == 202
    assert retry_resp.json()["status"] == "pending"


@pytest.mark.integration
async def test_ready_health_probe_api(api_client) -> None:
    resp = await api_client.get("/api/v1/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "checks" in data
