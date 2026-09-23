"""Integration tests for Authentication, Session Lifecycle, and RBAC APIs."""

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
from financial_rag.config.settings import DatabaseSettings, SecuritySettings, Settings
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


@pytest.fixture
async def auth_test_app(tmp_path):
    db_file = tmp_path / "auth_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    from pydantic import SecretStr

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("integration-test-secret-key-32chars-min!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
        auth_disabled_dev=False,  # Explicitly require auth
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

    return app


@pytest.mark.asyncio
async def test_auth_registration_and_login_flow(auth_test_app) -> None:
    transport = ASGITransport(app=auth_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new tenant owner
        reg_payload = {
            "email": "cfo@acmecorp.com",
            "password": "StrongPassword#2026",
            "tenant_name": "Acme Corp",
            "role": "owner",
        }
        reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_resp.status_code == 201
        reg_data = reg_resp.json()
        assert "access_token" in reg_data
        assert "refresh_token" in reg_data
        assert reg_data["role"] == "owner"
        access_token = reg_data["access_token"]
        refresh_token = reg_data["refresh_token"]

        # 2. Query /me with access token
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()
        assert me_data["email"] == "cfo@acmecorp.com"
        assert me_data["role"] == "owner"

        # 3. Test login with correct password
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "cfo@acmecorp.com", "password": "StrongPassword#2026"},
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data

        # 4. Test login with invalid password
        bad_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "cfo@acmecorp.com", "password": "WrongPassword123"},
        )
        assert bad_login.status_code == 401

        # 5. Rotate refresh token
        ref_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert ref_resp.status_code == 200
        ref_data = ref_resp.json()
        assert "access_token" in ref_data
        new_refresh = ref_data["refresh_token"]
        assert new_refresh != refresh_token

        # 6. Verify old refresh token is rejected (revoked)
        old_ref_resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert old_ref_resp.status_code == 401
