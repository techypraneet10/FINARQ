"""Phase 10 Security, IDOR, Authentication, Authorization & Rate Limit Verification Suite."""

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.api.dependencies import (
    get_audit_repository,
    get_db_session_manager,
    get_jwt_manager,
    get_password_hasher,
    get_refresh_token_repository,
    get_tenant_repository,
    get_user_repository,
)
from financial_rag.config.settings import (
    DatabaseSettings,
    SecuritySettings,
    Settings,
)
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresAuditEventRepository,
    PostgresRefreshTokenRepository,
    PostgresTenantRepository,
    PostgresUserRepository,
)
from financial_rag.infrastructure.security.hasher import ScryptPasswordHasher
from financial_rag.infrastructure.security.jwt import JwtTokenManager
from financial_rag.main import create_app
from tests.fixtures.pdf_fixtures import create_sample_10k_pdf


@pytest.fixture
async def sec_test_app(tmp_path):
    db_file = tmp_path / "sec_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    from pydantic import SecretStr

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("security-hardening-test-key-32ch!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
        auth_disabled_dev=False,
        rate_limit_enabled=True,
    )
    app_settings = Settings(security=sec_settings)
    app = create_app(settings=app_settings)

    tenant_repo = PostgresTenantRepository(session_manager=db_mgr)
    user_repo = PostgresUserRepository(session_manager=db_mgr)
    refresh_repo = PostgresRefreshTokenRepository(session_manager=db_mgr)
    audit_repo = PostgresAuditEventRepository(session_manager=db_mgr)
    hasher = ScryptPasswordHasher()
    jwt_mgr = JwtTokenManager(security_settings=sec_settings)

    app.dependency_overrides[get_db_session_manager] = lambda: db_mgr
    app.dependency_overrides[get_tenant_repository] = lambda: tenant_repo
    app.dependency_overrides[get_user_repository] = lambda: user_repo
    app.dependency_overrides[get_refresh_token_repository] = lambda: refresh_repo
    app.dependency_overrides[get_audit_repository] = lambda: audit_repo
    app.dependency_overrides[get_jwt_manager] = lambda: jwt_mgr
    app.dependency_overrides[get_password_hasher] = lambda: hasher

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {
            "client": client,
            "jwt_mgr": jwt_mgr,
            "user_repo": user_repo,
            "tenant_repo": tenant_repo,
        }

    app.dependency_overrides.clear()
    await db_mgr.close()


@pytest.mark.asyncio
async def test_authentication_error_scenarios(sec_test_app) -> None:
    client = sec_test_app["client"]

    # 1. Missing Authorization Header
    resp = await client.get("/api/v1/documents")
    assert resp.status_code == 401
    err = resp.json()
    assert "error" in err
    assert "Missing or malformed" in err["error"]["message"] or "error" in err

    # 2. Malformed Header (not Bearer)
    resp = await client.get("/api/v1/documents", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401

    # 3. Corrupted / Invalid JWT Token
    resp = await client.get(
        "/api/v1/documents", headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert resp.status_code == 401

    # 4. Expired JWT Token
    jwt_mgr = sec_test_app["jwt_mgr"]
    from financial_rag.domain.entities.security import UserRole

    expired_token = jwt_mgr.create_access_token(
        user_id="user-123",
        tenant_id="tenant-123",
        role=UserRole.MEMBER,
        expires_in_minutes=-10,
    )
    resp = await client.get(
        "/api/v1/documents", headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_file_upload_security_and_validation(sec_test_app) -> None:
    client = sec_test_app["client"]

    # Register user to get valid token
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "upload_sec@firm.com",
            "password": "UploadSec#2026!",
            "tenant_name": "Upload Sec Corp",
        },
    )
    assert reg_resp.status_code == 201
    token = reg_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Reject Empty File (0 bytes)
    empty_file = {"file": ("empty.pdf", b"", "application/pdf")}
    resp = await client.post("/api/v1/documents", headers=headers, files=empty_file)
    assert resp.status_code == 400

    # 2. Reject Non-PDF / Malicious executable disguised as PDF
    fake_pdf = {"file": ("malware.pdf", b"MZ\x90\x00\x03\x00\x00\x00", "application/pdf")}
    resp = await client.post("/api/v1/documents", headers=headers, files=fake_pdf)
    assert resp.status_code == 422
    assert "FILE_VALIDATION_ERROR" in resp.text or "magic header" in resp.text

    # 3. Path Traversal Filename Sanitization
    pdf_bytes = create_sample_10k_pdf()
    traversal_file = {
        "file": (
            "../../../../etc/passwd",
            pdf_bytes,
            "application/pdf",
        )
    }
    resp = await client.post("/api/v1/documents", headers=headers, files=traversal_file)
    assert resp.status_code == 202


@pytest.mark.asyncio
async def test_idor_cross_tenant_resource_isolation(sec_test_app) -> None:
    client = sec_test_app["client"]

    # Tenant A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@tenanta.com",
            "password": "AlicePassword#2026",
            "tenant_name": "Tenant A Org",
        },
    )
    token_a = reg_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Tenant B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "bob@tenantb.com",
            "password": "BobPassword#2026",
            "tenant_name": "Tenant B Org",
        },
    )
    token_b = reg_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant B uploads a document
    pdf_b = create_sample_10k_pdf()
    up_b = await client.post(
        "/api/v1/documents",
        headers=headers_b,
        files={"file": ("tenant_b.pdf", pdf_b, "application/pdf")},
        data={"title": "Tenant B Confidential Document"},
    )
    assert up_b.status_code == 202
    doc_b_id = up_b.json()["document_id"]
    job_b_id = up_b.json()["job_id"]

    # Alice (Tenant A) attempts to access Bob's document metadata -> 404
    resp = await client.get(f"/api/v1/documents/{doc_b_id}", headers=headers_a)
    assert resp.status_code == 404

    # Alice attempts to delete Bob's document -> 404
    resp = await client.delete(f"/api/v1/documents/{doc_b_id}", headers=headers_a)
    assert resp.status_code == 404

    # Alice attempts to access Bob's chunks -> 404
    resp = await client.get(f"/api/v1/documents/{doc_b_id}/chunks", headers=headers_a)
    assert resp.status_code == 404

    # Alice attempts to access Bob's pages -> 404
    resp = await client.get(f"/api/v1/documents/{doc_b_id}/pages", headers=headers_a)
    assert resp.status_code == 404

    # Alice attempts to access Bob's file binary -> 404
    resp = await client.get(f"/api/v1/documents/{doc_b_id}/file", headers=headers_a)
    assert resp.status_code == 404

    # Alice attempts to check Bob's ingestion job -> 404
    resp = await client.get(f"/api/v1/ingestion-jobs/{job_b_id}", headers=headers_a)
    assert resp.status_code == 404

    # Alice attempts to retry Bob's ingestion job -> 404
    resp = await client.post(f"/api/v1/ingestion-jobs/{job_b_id}/retry", headers=headers_a)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_brute_force_login_lockout(sec_test_app) -> None:
    client = sec_test_app["client"]

    # Register target account
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "lockout_target@example.com",
            "password": "CorrectPassword#123",
        },
    )
    assert reg_resp.status_code == 201

    # Attempt 5 consecutive failed logins
    for _ in range(5):
        fail_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "lockout_target@example.com", "password": "WrongPassword!"},
        )
        assert fail_resp.status_code == 401

    # 6th attempt should trigger 429 Too Many Requests lockout
    lock_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "lockout_target@example.com", "password": "WrongPassword!"},
    )
    assert lock_resp.status_code == 429
    assert "Retry-After" in lock_resp.headers
