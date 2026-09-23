"""End-to-End Cross-Tenant Security and Isolation Acceptance Test.

Critical Scenario:
- Tenant A registers and ingests Document A containing 'FY2023 Revenue was $100M'.
- Tenant B registers and ingests Document B containing 'FY2023 Revenue was $900M'.
- User A authenticates as Tenant A and queries 'What was the FY2023 Revenue?'.
- User A receives ONLY Tenant A evidence and facts ($100M).
- User A MUST NEVER see $900M or any evidence/chunks/citations from Document B.
- User A direct IDOR access attempts against Document B, Chunks B, and Ingestion Job B fail safely.
"""

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
from financial_rag.infrastructure.vector_store.qdrant import QdrantVectorStoreAdapter
from financial_rag.main import create_app
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.fixture
async def multi_tenant_app(tmp_path):
    # Setup test database
    db_file = tmp_path / "cross_tenant_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    from pydantic import SecretStr

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("e2e-isolation-test-key-32chars-min!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
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
    ver_repo = PostgresDocumentVersionRepository(session_manager=db_mgr)
    page_repo = PostgresDocumentPageRepository(session_manager=db_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=db_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=db_mgr)
    refresh_repo = PostgresRefreshTokenRepository(session_manager=db_mgr)
    audit_repo = PostgresAuditEventRepository(session_manager=db_mgr)
    hasher = ScryptPasswordHasher()
    jwt_mgr = JwtTokenManager(security_settings=sec_settings)

    embedder = MockEmbeddingProvider(dimension=1536)

    app.dependency_overrides[get_db_session_manager] = lambda: db_mgr
    app.dependency_overrides[get_tenant_repository] = lambda: tenant_repo
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_refresh_token_repository] = lambda: refresh_repo
    app.dependency_overrides[get_audit_repository] = lambda: audit_repo
    app.dependency_overrides[get_jwt_manager] = lambda: jwt_mgr
    app.dependency_overrides[get_password_hasher] = lambda: hasher
    app.dependency_overrides[get_vector_database] = lambda: vector_store
    app.dependency_overrides[get_embedding] = lambda: embedder

    return {
        "app": app,
        "db_mgr": db_mgr,
        "vector_store": vector_store,
        "doc_repo": doc_repo,
        "ver_repo": ver_repo,
        "page_repo": page_repo,
        "chunk_repo": chunk_repo,
        "job_repo": job_repo,
        "jwt_mgr": jwt_mgr,
        "embedder": embedder,
    }


@pytest.mark.asyncio
async def test_cross_tenant_isolation_and_idor_protection(multi_tenant_app) -> None:
    app = multi_tenant_app["app"]
    chunk_repo = multi_tenant_app["chunk_repo"]
    vector_store = multi_tenant_app["vector_store"]
    embedder = multi_tenant_app["embedder"]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register User A in Tenant A
        reg_a = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "alice@tenant-a.com",
                "password": "PasswordAlice#2026",
                "tenant_name": "Tenant A Corp",
                "role": "owner",
            },
        )
        assert reg_a.status_code == 201
        token_a = reg_a.json()["access_token"]
        tenant_a_id = reg_a.json()["tenant_id"]

        # 2. Register User B in Tenant B
        reg_b = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "bob@tenant-b.com",
                "password": "PasswordBob#2026",
                "tenant_name": "Tenant B Corp",
                "role": "owner",
            },
        )
        assert reg_b.status_code == 201
        token_b = reg_b.json()["access_token"]
        tenant_b_id = reg_b.json()["tenant_id"]

        # 3. Ingest Document A (Revenue = $100M) under Tenant A
        pdf_a_bytes = create_sample_10k_pdf()
        doc_a_resp = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token_a}"},
            files={"file": ("tenant_a_10k.pdf", pdf_a_bytes, "application/pdf")},
            data={"document_type": "10-K", "ticker_symbol": "TA", "fiscal_year": 2023},
        )
        assert doc_a_resp.status_code == 202
        doc_a_id = doc_a_resp.json()["document_id"]

        # 4. Ingest Document B (Revenue = $900M) under Tenant B
        pdf_b_bytes = create_sample_10k_pdf()
        doc_b_resp = await client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token_b}"},
            files={"file": ("tenant_b_10k.pdf", pdf_b_bytes, "application/pdf")},
            data={"document_type": "10-K", "ticker_symbol": "TB", "fiscal_year": 2023},
        )
        assert doc_b_resp.status_code == 202
        doc_b_id = doc_b_resp.json()["document_id"]
        job_b_id = doc_b_resp.json()["job_id"]

        # Seed indexed chunk with $100M for Tenant A and $900M for Tenant B into vector store & db
        # Tenant A chunk
        chunk_a_content = "Tenant A Corp reported Total Revenue of $100 million for FY2023."
        emb_a = await embedder.embed_text(chunk_a_content)
        chunk_a_obj = DocumentChunk(
            id=str(uuid4()),
            tenant_id=tenant_a_id,
            document_id=doc_a_id,
            document_version_id=doc_a_resp.json()["version_id"],
            page_number=1,
            chunk_index=0,
            chunk_type=ChunkType.TEXT,
            content=chunk_a_content,
            token_count=15,
            char_count=len(chunk_a_content),
        )
        await chunk_repo.save(chunk_a_obj)
        await vector_store.upsert_chunks([chunk_a_obj], [emb_a])

        # Tenant B chunk
        chunk_b_content = "Tenant B Corp reported Total Revenue of $900 million for FY2023."
        emb_b = await embedder.embed_text(chunk_b_content)
        chunk_b_obj = DocumentChunk(
            id=str(uuid4()),
            tenant_id=tenant_b_id,
            document_id=doc_b_id,
            document_version_id=doc_b_resp.json()["version_id"],
            page_number=1,
            chunk_index=0,
            chunk_type=ChunkType.TEXT,
            content=chunk_b_content,
            token_count=15,
            char_count=len(chunk_b_content),
        )
        await chunk_repo.save(chunk_b_obj)
        await vector_store.upsert_chunks([chunk_b_obj], [emb_b])

        # 5. TEST CROSS-TENANT RAG RETRIEVAL ISOLATION
        # User A executes search for "What was the total revenue?"
        search_a = await client.post(
            "/api/v1/retrieval/search",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"query": "What was the total revenue?", "top_k": 10},
        )
        assert search_a.status_code == 200
        search_data = search_a.json()

        # MUST contain Tenant A evidence ($100M)
        assert any("100" in item["content"] for item in search_data["evidence"])
        # MUST NEVER contain Tenant B evidence ($900M)
        assert not any("900" in item["content"] for item in search_data["evidence"])
        assert not any(item["document_id"] == doc_b_id for item in search_data["evidence"])

        # 6. TEST CROSS-TENANT ANSWER GENERATION ISOLATION
        answer_a = await client.post(
            "/api/v1/answers",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"query": "What was the total revenue for FY2023?"},
        )
        assert answer_a.status_code == 200
        ans_data = answer_a.json()
        assert ans_data["status"] in ["completed", "partially_answered", "insufficient_evidence"]
        # Must NEVER mention Tenant B numbers ($900M)
        assert "900" not in ans_data.get("answer_text", "")
        # Must cite only Document A, never Document B
        for cit in ans_data.get("citations", []):
            assert cit["document_id"] == doc_a_id
            assert cit["document_id"] != doc_b_id

        # 7. TEST DIRECT IDOR ATTACKS BY USER A AGAINST TENANT B RESOURCES
        # 7a. User A attempts to read Document B
        idor_doc = await client.get(
            f"/api/v1/documents/{doc_b_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert idor_doc.status_code == 404  # Safe 404 Not Found

        # 7b. User A attempts to list chunks of Document B
        idor_chunks = await client.get(
            f"/api/v1/documents/{doc_b_id}/chunks",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert idor_chunks.status_code == 404

        # 7c. User A attempts to read Ingestion Job B
        idor_job = await client.get(
            f"/api/v1/ingestion-jobs/{job_b_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert idor_job.status_code == 404

        # 7d. User A attempts to delete Document B
        idor_del = await client.delete(
            f"/api/v1/documents/{doc_b_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert idor_del.status_code == 404

        # 7e. User A queries documents list -> must contain Doc A, never Doc B
        list_docs_a = await client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert list_docs_a.status_code == 200
        docs_list = list_docs_a.json()
        doc_ids = [d["id"] for d in docs_list]
        assert doc_a_id in doc_ids
        assert doc_b_id not in doc_ids
