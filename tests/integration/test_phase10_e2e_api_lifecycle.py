"""Phase 10 Critical End-to-End API Lifecycle Acceptance Test.

Verifies the complete flow through FastAPI orchestration boundary:
AUTHENTICATE
     ↓
UPLOAD FINANCIAL PDF
     ↓
INGESTION JOB CREATED
     ↓
POLL JOB STATUS
     ↓
SEARCH EVIDENCE (/api/v1/search and /api/v1/retrieval/search)
     ↓
REASONING ANSWER PACKAGE (/api/v1/reasoning/answer-package)
     ↓
ASK QUESTION & SYNTHESIZE ANSWER (/api/v1/answers)
     ↓
STREAM ANSWER SSE (/api/v1/answers/stream)
     ↓
ASSERT FRONTEND CONTRACT COMPATIBILITY
"""

import json
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.api.dependencies import (
    get_audit_repository,
    get_db_session_manager,
    get_embedding,
    get_jwt_manager,
    get_password_hasher,
    get_refresh_token_repository,
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
from financial_rag.domain.entities.models import (
    ChunkType,
    DocumentChunk,
)
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
from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher
from financial_rag.infrastructure.security.jwt import JwtTokenManager
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter
from financial_rag.main import create_app
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.fixture
async def e2e_app_client(tmp_path):
    db_file = tmp_path / "e2e_lifecycle.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    from pydantic import SecretStr

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("phase10-e2e-super-secret-key-32ch!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=30,
        refresh_token_ttl_days=7,
        auth_disabled_dev=False,
    )
    app_settings = Settings(security=sec_settings)
    app = create_app(settings=app_settings)

    vector_store = QdrantVectorStoreAdapter(
        qdrant_settings=QdrantSettings(collection_name="financial_chunks", location=":memory:")
    )
    await vector_store.initialize_collection(dimension=1536)

    tenant_repo = PostgresTenantRepository(session_manager=db_mgr)
    user_repo = PostgresUserRepository(session_manager=db_mgr)
    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)
    refresh_repo = PostgresRefreshTokenRepository(session_manager=db_mgr)
    audit_repo = PostgresAuditEventRepository(session_manager=db_mgr)
    hasher = ScryptPasswordHasher()
    jwt_mgr = JwtTokenManager(security_settings=sec_settings)
    embedder = MockEmbeddingProvider(dimension=1536)

    from financial_rag.api.dependencies import get_sparse_retriever
    from financial_rag.infrastructure.retrieval.sparse_retriever import BM25SparseRetriever

    sparse_retriever = BM25SparseRetriever()

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
async def test_complete_phase10_api_lifecycle(e2e_app_client) -> None:
    client = e2e_app_client["client"]
    chunk_repo = e2e_app_client["chunk_repo"]
    vector_store = e2e_app_client["vector_store"]
    embedder = e2e_app_client["embedder"]

    # 1. AUTHENTICATE - Register User & Tenant
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "analyst@hedgefund.com",
            "password": "StrongPassword#2026",
            "tenant_name": "Apex Capital",
            "role": "owner",
        },
    )
    assert reg_resp.status_code == 201
    auth_data = reg_resp.json()
    assert "access_token" in auth_data
    assert "refresh_token" in auth_data
    token = auth_data["access_token"]
    tenant_id = auth_data["tenant_id"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    # Verify /api/v1/auth/me
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "analyst@hedgefund.com"

    # 2. UPLOAD FINANCIAL PDF
    pdf_bytes = create_sample_10k_pdf()
    files = {"file": ("apple_10k_fy24.pdf", pdf_bytes, "application/pdf")}
    data = {
        "document_type": "10-K",
        "title": "Apple Inc. FY2024 Form 10-K",
        "ticker_symbol": "AAPL",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
    }
    upload_resp = await client.post(
        "/api/v1/documents",
        headers=auth_headers,
        files=files,
        data=data,
    )
    assert upload_resp.status_code == 202
    upload_json = upload_resp.json()
    assert "document_id" in upload_json
    assert "version_id" in upload_json
    assert "job_id" in upload_json
    doc_id = upload_json["document_id"]
    version_id = upload_json["version_id"]
    job_id = upload_json["job_id"]

    # 3. POLL INGESTION JOB STATUS
    job_resp = await client.get(f"/api/v1/ingestion-jobs/{job_id}", headers=auth_headers)
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["document_id"] == doc_id
    assert job_data["status"] in ["pending", "processing", "completed"]

    # Verify GET /api/v1/ingestion-jobs list endpoint
    jobs_list_resp = await client.get("/api/v1/ingestion-jobs", headers=auth_headers)
    assert jobs_list_resp.status_code == 200
    jobs_list = jobs_list_resp.json()
    assert isinstance(jobs_list, list)
    assert any(j["id"] == job_id for j in jobs_list)

    # Also verify /api/v1/documents/jobs/{job_id} alias
    doc_job_resp = await client.get(f"/api/v1/documents/jobs/{job_id}", headers=auth_headers)
    assert doc_job_resp.status_code == 200

    # Seed structured financial chunk to verify downstream search, reasoning, and answer flow
    chunk_content = (
        "Apple Inc. Net Sales for the fiscal year ended September 28, 2024 was $391,035 million, "
        "compared to $383,285 million for the fiscal year ended September 30, 2023."
    )
    emb = await embedder.embed_text(chunk_content)
    chunk_obj = DocumentChunk(
        id=str(uuid4()),
        tenant_id=tenant_id,
        document_id=doc_id,
        document_version_id=version_id,
        page_number=45,
        chunk_index=0,
        chunk_type=ChunkType.TEXT,
        content=chunk_content,
        section_path="Item 7. Management's Discussion and Analysis",
        token_count=35,
        char_count=len(chunk_content),
    )
    sparse_retriever = e2e_app_client["sparse_retriever"]
    await chunk_repo.save(chunk_obj)
    await vector_store.upsert_chunks([chunk_obj], [emb])
    await sparse_retriever.index_chunks([chunk_obj])

    # 4. SEARCH EVIDENCE via /api/v1/search and /api/v1/retrieval/search
    search_payload = {
        "query": "What was Apple's total net sales in fiscal year 2024?",
        "top_k": 5,
        "filters": {"ticker_symbols": ["AAPL"]},
    }
    # Canonical /api/v1/search
    search_resp = await client.post("/api/v1/search", headers=auth_headers, json=search_payload)
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert "evidence" in search_data
    assert len(search_data["evidence"]) >= 1
    assert any("391,035" in ev["content"] for ev in search_data["evidence"])

    # Retrieval router /api/v1/retrieval/search
    retrieval_resp = await client.post(
        "/api/v1/retrieval/search", headers=auth_headers, json=search_payload
    )
    assert retrieval_resp.status_code == 200

    # 5. REASONING ENGINE - AnswerPackage Generation
    reasoning_resp = await client.post(
        "/api/v1/reasoning/answer-package",
        headers=auth_headers,
        json={"query": "What was Apple's revenue in 2024 and 2023?", "top_k": 5},
    )
    assert reasoning_resp.status_code == 200
    pkg = reasoning_resp.json()
    assert "package_id" in pkg
    assert "answerability" in pkg
    assert "facts" in pkg
    assert "claims" in pkg
    assert "citations" in pkg

    # 6. VERIFIED ANSWER SYNTHESIS
    answer_resp = await client.post(
        "/api/v1/answers",
        headers=auth_headers,
        json={
            "query": "What was Apple's total revenue in fiscal year 2024?",
            "response_style": "standard",
            "include_citations": True,
            "top_k": 5,
        },
    )
    assert answer_resp.status_code == 200
    ans_json = answer_resp.json()
    assert "answer_id" in ans_json
    assert ans_json["status"] in [
        "completed",
        "partially_answered",
        "insufficient_evidence",
    ]
    assert "answer" in ans_json
    assert "citations" in ans_json
    assert "metadata" in ans_json

    # 7. SERVER-SENT EVENTS STREAMING
    stream_resp = await client.post(
        "/api/v1/answers/stream",
        headers=auth_headers,
        json={
            "query": "What was Apple's total revenue in fiscal year 2024?",
            "top_k": 5,
        },
    )
    assert stream_resp.status_code == 200
    assert "text/event-stream" in stream_resp.headers["content-type"]
    lines = stream_resp.text.strip().split("\n\n")
    events = [json.loads(line[6:]) for line in lines if line.startswith("data: ")]
    assert len(events) >= 1
    event_types = [e["event_type"] for e in events]
    assert any(t in event_types for t in ["stage_start", "reasoning_complete", "answer_complete"])

    # 8. VERIFY DOCUMENT METADATA AND FILE DOWNLOAD
    doc_detail = await client.get(f"/api/v1/documents/{doc_id}", headers=auth_headers)
    assert doc_detail.status_code == 200
    assert doc_detail.json()["title"] == "Apple Inc. FY2024 Form 10-K"

    doc_file = await client.get(f"/api/v1/documents/{doc_id}/file", headers=auth_headers)
    assert doc_file.status_code == 200
    assert doc_file.headers["content-type"] == "application/pdf"
    assert len(doc_file.content) > 0
