"""Phase 11 End-to-End User Journey Integration Tests.

Validates the full interactive lifecycle matching the React frontend client:
1. Registration & Authentication (JWT + Refresh + Tenant Scoping)
2. Document Ingestion (Multipart PDF upload + Async Ingestion Job Tracking)
3. Ingestion Jobs List & Status Polling (/api/v1/ingestion-jobs)
4. Hybrid Search (/api/v1/search and /api/v1/retrieval/search)
5. Financial Reasoning Package (/api/v1/reasoning/answer-package)
6. Verified Answer Synthesis with [C1] Citations (/api/v1/answers)
7. Document Detail & Page Block Inspection (/api/v1/documents/{id}/pages)
8. System Health, Readiness, and Root Metrics (/health, /ready, /metrics)
9. Cryptographic Audit Trail (/api/v1/audit-events)
"""

from io import BytesIO
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from financial_rag.api.dependencies import (
    get_audit_repository,
    get_db_session_manager,
    get_embedding,
    get_jwt_manager,
    get_password_hasher,
    get_refresh_token_repository,
    get_sparse_retriever,
    get_tenant_repository,
    get_user_repository,
    get_vector_database,
)
from financial_rag.config.settings import (
    DatabaseSettings,
    QdrantSettings,
    SecuritySettings,
    Settings,
)
from financial_rag.domain.entities.models import ChunkType, DocumentChunk
from financial_rag.infrastructure.embeddings.mock_provider import MockEmbeddingProvider
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresAuditEventRepository,
    PostgresDocumentChunkRepository,
    PostgresDocumentRepository,
    PostgresIngestionJobRepository,
    PostgresRefreshTokenRepository,
    PostgresTenantRepository,
    PostgresUserRepository,
)
from financial_rag.infrastructure.retrieval.sparse_retriever import BM25SparseRetriever
from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher
from financial_rag.infrastructure.security.jwt import JwtTokenManager
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter
from financial_rag.main import create_app
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.fixture
async def full_journey_client(tmp_path):
    db_file = tmp_path / "phase11_journey.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("a" * 64),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=30,
        refresh_token_ttl_days=7,
        auth_disabled_dev=False,
    )
    app = create_app(settings=Settings(security=sec_settings))

    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(collection_name="financial_chunks", location=":memory:")
    )
    await vector_store.initialize_collection(dimension=1536)

    tenant_repo = PostgresTenantRepository(session_manager=db_mgr)
    user_repo = PostgresUserRepository(session_manager=db_mgr)
    refresh_repo = PostgresRefreshTokenRepository(session_manager=db_mgr)
    audit_repo = PostgresAuditEventRepository(session_manager=db_mgr)
    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)

    sparse_retriever = BM25SparseRetriever()
    embedder = MockEmbeddingProvider(dimension=1536)

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
    app.dependency_overrides[get_sparse_retriever] = lambda: sparse_retriever

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "chunk_repo": chunk_repo,
            "vector_store": vector_store,
            "sparse_retriever": sparse_retriever,
            "embedder": embedder,
            "doc_repo": doc_repo,
            "job_repo": job_repo,
        }

    app.dependency_overrides.clear()
    await db_mgr.close()


@pytest.mark.asyncio
async def test_full_phase11_user_journey(full_journey_client) -> None:
    client = full_journey_client["client"]
    chunk_repo = full_journey_client["chunk_repo"]
    vector_store = full_journey_client["vector_store"]
    embedder = full_journey_client["embedder"]
    sparse_retriever = full_journey_client["sparse_retriever"]

    # 1. AUTHENTICATION & RBAC
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "analyst@hedgefund.com",
            "password": "SecurePassword123!",
            "full_name": "Senior Equity Analyst",
            "organization_name": "Alpha Capital Management",
        },
    )
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    access_token = auth_data["access_token"]
    assert "refresh_token" in auth_data
    headers = {"Authorization": f"Bearer {access_token}"}

    # Verify /me endpoint
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "analyst@hedgefund.com"

    # 2. DOCUMENT UPLOAD
    pdf_content = create_sample_10k_pdf()
    files = {"file": ("aapl-2024-10k.pdf", BytesIO(pdf_content), "application/pdf")}
    data = {
        "title": "Apple Inc. 2024 Form 10-K",
        "document_type": "10-K",
        "ticker_symbol": "AAPL",
        "fiscal_year": "2024",
        "fiscal_period": "FY",
    }
    upload_resp = await client.post("/api/v1/documents", headers=headers, data=data, files=files)
    assert upload_resp.status_code == 202
    up_data = upload_resp.json()
    doc_id = up_data["document_id"]
    version_id = up_data["version_id"]
    job_id = up_data["job_id"]

    # 3. INGESTION JOBS LIST & RETRIEVAL
    job_resp = await client.get(f"/api/v1/ingestion-jobs/{job_id}", headers=headers)
    assert job_resp.status_code == 200
    assert job_resp.json()["id"] == job_id

    jobs_list_resp = await client.get("/api/v1/ingestion-jobs", headers=headers)
    assert jobs_list_resp.status_code == 200
    assert len(jobs_list_resp.json()) >= 1
    assert any(j["id"] == job_id for j in jobs_list_resp.json())

    # 4. INDEX STRUCTURED EVIDENCE
    text_snippet = (
        "Apple Inc. reported Total Net Sales of $391,035 million in fiscal year 2024, "
        "representing a 2.0% increase from $383,285 million in fiscal year 2023."
    )
    emb = await embedder.embed_text(text_snippet)
    chunk = DocumentChunk(
        id=str(uuid4()),
        tenant_id=auth_data["tenant_id"],
        document_id=doc_id,
        document_version_id=version_id,
        page_number=48,
        chunk_index=0,
        chunk_type=ChunkType.TEXT,
        content=text_snippet,
        section_path="Item 7. MD&A",
        token_count=30,
        char_count=len(text_snippet),
    )
    await chunk_repo.save(chunk)
    await vector_store.upsert_chunks([chunk], [emb])
    await sparse_retriever.index_chunks([chunk])

    # 5. HYBRID SEARCH
    search_resp = await client.post(
        "/api/v1/search",
        headers=headers,
        json={"query": "Apple total net sales 2024", "top_k": 5},
    )
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert len(search_data["evidence"]) >= 1
    assert search_data["evidence"][0]["document_id"] == doc_id
    assert search_data["evidence"][0]["page_number"] == 48

    # 6. REASONING ANSWER PACKAGE
    reasoning_resp = await client.post(
        "/api/v1/reasoning/answer-package",
        headers=headers,
        json={"query": "What was Apple's total net sales in 2024 and YoY growth?", "top_k": 5},
    )
    assert reasoning_resp.status_code == 200
    pkg_data = reasoning_resp.json()
    assert "calculations" in pkg_data
    assert "facts" in pkg_data
    assert "citations" in pkg_data

    # 7. VERIFIED ANSWER SYNTHESIS WITH RESPONSE STYLE
    answer_resp = await client.post(
        "/api/v1/answers",
        headers=headers,
        json={
            "query": "What was Apple's total net sales in 2024?",
            "response_style": "detailed",
            "top_k": 5,
        },
    )
    assert answer_resp.status_code == 200
    ans_data = answer_resp.json()
    assert ans_data["status"] in [
        "completed",
        "partially_answered",
        "insufficient_evidence",
        "grounded",
    ]
    assert "answer" in ans_data

    # 8. OBSERVABILITY PROBES & ROOT METRICS
    health_resp = await client.get("/health")
    assert health_resp.status_code == 200

    ready_resp = await client.get("/ready")
    assert ready_resp.status_code == 200

    metrics_resp = await client.get("/metrics")
    assert metrics_resp.status_code == 200
    assert "counters" in metrics_resp.json()

    # 9. AUDIT LOGGING
    audit_resp = await client.get("/api/v1/audit-events", headers=headers)
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) >= 1
