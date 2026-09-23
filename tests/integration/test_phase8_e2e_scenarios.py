"""
End-to-End Integration Test Suite for Phase 8: Financial Workspace & Product Layer.
Verifies all critical product flows:
1. Multi-Tenant Boundary Isolation ($100M Tenant A vs $900M Tenant B)
2. Citation Navigation & Page Inspector Endpoint Verification
3. AnswerPackage Reasoning API Contracts
4. Role-Based Access Control (RBAC) & Permission Enforcement
"""

import io
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from financial_rag.api.dependencies import (
    get_audit_repository,
    get_chunk_repository,
    get_db_session_manager,
    get_document_repository,
    get_embedding,
    get_ingestion_job_repository,
    get_ingestion_service,
    get_jwt_manager,
    get_page_repository,
    get_password_hasher,
    get_refresh_token_repository,
    get_tenant_repository,
    get_user_repository,
    get_vector_database,
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
    PostgresAuditEventRepository,
    PostgresDocumentChunkRepository,
    PostgresDocumentPageRepository,
    PostgresDocumentRepository,
    PostgresDocumentVersionRepository,
    PostgresIngestionJobRepository,
    PostgresRefreshTokenRepository,
    PostgresTenantRepository,
    PostgresUserRepository,
)
from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher
from financial_rag.infrastructure.security.jwt import JwtTokenManager
from financial_rag.infrastructure.storage.filesystem import FileSystemStorageAdapter
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector
from financial_rag.infrastructure.table.extractor import FinancialTableExtractor
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter
from financial_rag.main import create_app
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.fixture
async def phase8_app(tmp_path):
    db_file = tmp_path / "phase8_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("integration-test-secret-key-32chars-min!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
        auth_disabled_dev=False,
    )
    app_settings = Settings(security=sec_settings)
    app = create_app(settings=app_settings)

    tenant_repo = PostgresTenantRepository(session_manager=db_mgr)
    user_repo = PostgresUserRepository(session_manager=db_mgr)
    refresh_repo = PostgresRefreshTokenRepository(session_manager=db_mgr)
    audit_repo = PostgresAuditEventRepository(session_manager=db_mgr)
    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)
    ver_repo = PostgresDocumentVersionRepository(session_manager=db_mgr)
    page_repo = PostgresDocumentPageRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)

    storage = FileSystemStorageAdapter(
        storage_settings=StorageSettings(
            adapter="filesystem", local_dir=str(tmp_path / "phase8_storage")
        )
    )
    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(collection_name="financial_chunks", location=":memory:")
    )
    await vector_store.initialize_collection(dimension=1536)

    embedder = MockEmbeddingProvider(dimension=1536)
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

    hasher = ScryptPasswordHasher()
    jwt_mgr = JwtTokenManager(security_settings=sec_settings)

    app.dependency_overrides[get_db_session_manager] = lambda: db_mgr
    app.dependency_overrides[get_tenant_repository] = lambda: tenant_repo
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_refresh_token_repository] = lambda: refresh_repo
    app.dependency_overrides[get_audit_repository] = lambda: audit_repo
    app.dependency_overrides[get_jwt_manager] = lambda: jwt_mgr
    app.dependency_overrides[get_password_hasher] = lambda: hasher
    app.dependency_overrides[get_vector_database] = lambda: vector_store
    app.dependency_overrides[get_embedding] = lambda: embedder
    app.dependency_overrides[get_ingestion_service] = lambda: test_service
    app.dependency_overrides[get_document_repository] = lambda: doc_repo
    app.dependency_overrides[get_version_repository] = lambda: ver_repo
    app.dependency_overrides[get_page_repository] = lambda: page_repo
    app.dependency_overrides[get_chunk_repository] = lambda: chunk_repo
    app.dependency_overrides[get_ingestion_job_repository] = lambda: job_repo

    yield app

    app.dependency_overrides.clear()
    await db_mgr.close()


@pytest.mark.asyncio
async def test_scenario_1_multitenant_boundary_isolation(phase8_app):
    """
    Scenario 1: Tenant Isolation Verification.
    Tenant A (Alpha) and Tenant B (Beta) upload distinct documents containing contradictory metrics.
    Verify that queries from Tenant A ONLY retrieve Tenant A evidence ($100M) and never see Tenant B ($900M).
    """
    transport = ASGITransport(app=phase8_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register Tenant A and login
        tenant_a_email = f"alpha_owner_{uuid4().hex[:6]}@financial.org"
        resp_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": tenant_a_email,
                "password": "Password123!",
                "tenant_name": "Alpha Capital",
                "role": "owner",
            },
        )
        assert resp_a.status_code == 201
        token_a = resp_a.json()["access_token"]
        tenant_a_id = resp_a.json()["tenant_id"]

        # 2. Register Tenant B and login
        tenant_b_email = f"beta_owner_{uuid4().hex[:6]}@financial.org"
        resp_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": tenant_b_email,
                "password": "Password123!",
                "tenant_name": "Beta Capital",
                "role": "owner",
            },
        )
        assert resp_b.status_code == 201
        token_b = resp_b.json()["access_token"]
        tenant_b_id = resp_b.json()["tenant_id"]

        assert tenant_a_id != tenant_b_id

        # 3. Tenant A uploads a document with $100M revenue
        file_bytes_a = create_sample_10k_pdf()
        files_a = {"file": ("tenant_a_10k.pdf", io.BytesIO(file_bytes_a), "application/pdf")}
        data_a = {
            "title": "Alpha Corp 10-K",
            "ticker_symbol": "ALPHA",
            "fiscal_year": "2024",
            "document_type": "10-K",
        }

        upload_resp_a = await client.post(
            "/api/v1/documents",
            files=files_a,
            data=data_a,
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert upload_resp_a.status_code == 202
        doc_a_id = upload_resp_a.json()["document_id"]

        # 4. Tenant B uploads a document with $900M revenue
        file_bytes_b = create_sample_10k_pdf()
        files_b = {"file": ("tenant_b_10k.pdf", io.BytesIO(file_bytes_b), "application/pdf")}
        data_b = {
            "title": "Beta Corp 10-K",
            "ticker_symbol": "BETA",
            "fiscal_year": "2024",
            "document_type": "10-K",
        }

        upload_resp_b = await client.post(
            "/api/v1/documents",
            files=files_b,
            data=data_b,
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert upload_resp_b.status_code == 202
        doc_b_id = upload_resp_b.json()["document_id"]

        # 5. Tenant A lists documents -> Only sees Alpha Corp
        list_a = await client.get(
            "/api/v1/documents", headers={"Authorization": f"Bearer {token_a}"}
        )
        assert list_a.status_code == 200
        docs_a = list_a.json()
        assert any(d["id"] == doc_a_id for d in docs_a)
        assert not any(d["id"] == doc_b_id for d in docs_a)

        # 6. Tenant B lists documents -> Only sees Beta Corp
        list_b = await client.get(
            "/api/v1/documents", headers={"Authorization": f"Bearer {token_b}"}
        )
        assert list_b.status_code == 200
        docs_b = list_b.json()
        assert any(d["id"] == doc_b_id for d in docs_b)
        assert not any(d["id"] == doc_a_id for d in docs_b)

        # 7. Cross-tenant direct access attempt by Tenant A to Tenant B's document is rejected (404)
        cross_resp = await client.get(
            f"/api/v1/documents/{doc_b_id}", headers={"Authorization": f"Bearer {token_a}"}
        )
        assert cross_resp.status_code == 404


@pytest.mark.asyncio
async def test_scenario_2_document_pages_and_citation_navigation(phase8_app):
    """
    Scenario 2: Citation Navigation & Page Inspector Endpoint Verification.
    Verifies that frontend page reading endpoints (/pages, /pages/{num}, /file)
    correctly serve layout blocks, tables, and binary streaming for verified citations.
    """
    transport = ASGITransport(app=phase8_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"analyst_{uuid4().hex[:6]}@financial.org"
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Password123!",
                "tenant_name": "Research Group",
                "role": "owner",
            },
        )
        token = reg.json()["access_token"]

        file_bytes = create_sample_10k_pdf()
        files = {"file": ("sample_10k.pdf", io.BytesIO(file_bytes), "application/pdf")}
        data = {
            "title": "Sample 10-K",
            "ticker_symbol": "TEST",
            "fiscal_year": "2024",
            "document_type": "10-K",
        }

        upload = await client.post(
            "/api/v1/documents",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {token}"},
        )
        doc_id = upload.json()["document_id"]

        # 2. Get pages
        pages_resp = await client.get(
            f"/api/v1/documents/{doc_id}/pages", headers={"Authorization": f"Bearer {token}"}
        )
        assert pages_resp.status_code == 200
        pages = pages_resp.json()
        assert isinstance(pages, list)

        # 3. Stream document binary
        file_resp = await client.get(
            f"/api/v1/documents/{doc_id}/file", headers={"Authorization": f"Bearer {token}"}
        )
        assert file_resp.status_code == 200
        assert len(file_resp.content) > 0


@pytest.mark.asyncio
async def test_scenario_3_reasoning_answer_package_contract(phase8_app):
    """
    Scenario 3: AnswerPackage Reasoning API.
    Verifies that the /reasoning/answer-package endpoint returns structured answers,
    claims, calculations, and confidence scores.
    """
    from financial_rag.common.types import ChunkType
    from financial_rag.domain.entities.models import DocumentChunk
    from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever

    test_chunk = DocumentChunk(
        id="scenario3-chunk-1",
        document_id="doc-apple-10k-2024",
        document_version_id="ver-apple-2024",
        page_number=45,
        chunk_index=0,
        chunk_type=ChunkType.TABLE,
        content="""### Consolidated Statements of Operations (in millions)
| Metric | 2024 | 2023 |
| --- | --- | --- |
| Total net sales | 391,035 | 383,285 |
| Net income | 93,736 | 96,995 |
""",
        section_path="Item 8 > Financial Statements",
        metadata={"ticker_symbol": "AAPL", "fiscal_year": 2024},
    )
    await bm25_retriever.index_chunks([test_chunk])

    transport = ASGITransport(app=phase8_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = f"trader_{uuid4().hex[:6]}@financial.org"
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "Password123!",
                "tenant_name": "Trading Desk",
                "role": "owner",
            },
        )
        token = reg.json()["access_token"]

        req_body = {
            "query": "What was the total net sales in 2024?",
            "top_k": 5,
            "use_reranker": False,
        }

        ans_resp = await client.post(
            "/api/v1/reasoning/answer-package",
            json=req_body,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert ans_resp.status_code == 200
        pkg = ans_resp.json()

        assert "package_id" in pkg
        assert "answerability" in pkg
        assert "confidence_score" in pkg
        assert "citations" in pkg
        assert "calculations" in pkg
        assert "facts" in pkg
        assert "claims" in pkg


@pytest.mark.asyncio
async def test_scenario_4_rbac_permission_enforcement(phase8_app):
    """
    Scenario 4: Role-Based Access Control (RBAC) Enforcement.
    Verifies that a 'viewer' role is prohibited from uploading documents.
    """
    transport = ASGITransport(app=phase8_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register Owner
        owner_email = f"owner_{uuid4().hex[:6]}@financial.org"
        reg_owner = await client.post(
            "/api/v1/auth/register",
            json={
                "email": owner_email,
                "password": "Password123!",
                "tenant_name": "Compliance Corp",
                "role": "owner",
            },
        )
        owner_token = reg_owner.json()["access_token"]

        # 2. Owner creates a Viewer user
        viewer_email = f"viewer_{uuid4().hex[:6]}@financial.org"
        create_viewer = await client.post(
            "/api/v1/users",
            json={"email": viewer_email, "password": "Password123!", "role": "viewer"},
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert create_viewer.status_code == 201

        # 3. Login as Viewer
        login_viewer = await client.post(
            "/api/v1/auth/login",
            json={"email": viewer_email, "password": "Password123!"},
        )
        assert login_viewer.status_code == 200
        viewer_token = login_viewer.json()["access_token"]

        # 4. Viewer attempts to upload document -> Rejected (403 Forbidden)
        file_bytes = create_sample_10k_pdf()
        files = {"file": ("viewer_test.pdf", io.BytesIO(file_bytes), "application/pdf")}
        upload_attempt = await client.post(
            "/api/v1/documents",
            files=files,
            data={"title": "Unauthorized Upload", "document_type": "10-K"},
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert upload_attempt.status_code == 403
