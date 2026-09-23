"""Phase 15 Deployment Readiness, Migration, Health Probes & Release Verification Suite."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from financial_rag.api.dependencies import get_db_session_manager
from financial_rag.common.types import Environment
from financial_rag.config.settings import (
    AppSettings,
    DatabaseSettings,
    QdrantSettings,
    SecuritySettings,
    Settings,
    validate_security_configuration,
)
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.main import create_app


@pytest.fixture
async def deployment_test_app(tmp_path):
    """Create isolated FastAPI app instance configured for deployment verification."""
    db_file = tmp_path / "deploy_test.db"
    db_mgr = DatabaseSessionManager(
        db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    )
    await db_mgr.create_all_tables()

    sec_settings = SecuritySettings(
        jwt_secret_key=SecretStr("phase15-production-deployment-key-32ch!"),
        jwt_algorithm="HS256",
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=7,
        auth_disabled_dev=False,
    )
    app_settings = Settings(
        app=AppSettings(
            environment=Environment.PRODUCTION,
            debug=False,
            name="FINARQ",
            version="1.0.0",
            git_sha="deploy-test-sha123",
            cors_origins=["https://app.financial-rag.example.com"],
        ),
        security=sec_settings,
        qdrant=QdrantSettings(location=":memory:", collection_name="deploy_test_col"),
    )
    app = create_app(settings=app_settings)
    app.dependency_overrides[get_db_session_manager] = lambda: db_mgr

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield {"app": app, "client": client, "settings": app_settings, "db_mgr": db_mgr}

    app.dependency_overrides.clear()
    await db_mgr.close()


@pytest.mark.asyncio
async def test_readiness_probe_healthy_dependencies(deployment_test_app) -> None:
    """Verify that /ready probe reports operational status across all adapters."""
    client: AsyncClient = deployment_test_app["client"]

    resp = await client.get("/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ready", "degraded")
    assert "checks" in data
    assert "database" in data["checks"]
    assert "object_storage" in data["checks"]
    assert "vector_store" in data["checks"]
    assert "embedding_provider" in data["checks"]


@pytest.mark.asyncio
async def test_production_configuration_fail_fast_validation() -> None:
    """Verify that invalid production settings fail fast on startup."""
    # 1. Reject auth_disabled_dev in production
    bad_sec_1 = SecuritySettings(
        jwt_secret_key=SecretStr("long-enough-secret-key-32chars-min!"),
        auth_disabled_dev=True,
    )
    bad_app_1 = Settings(app=AppSettings(environment=Environment.PRODUCTION), security=bad_sec_1)
    with pytest.raises(ValueError) as exc1:
        validate_security_configuration(settings=bad_app_1)
    assert "auth_disabled_dev" in str(exc1.value)

    # 2. Reject short JWT secret key in production
    bad_sec_2 = SecuritySettings(
        jwt_secret_key=SecretStr("short-secret"),
        auth_disabled_dev=False,
    )
    bad_app_2 = Settings(app=AppSettings(environment=Environment.PRODUCTION), security=bad_sec_2)
    with pytest.raises(ValueError) as exc2:
        validate_security_configuration(settings=bad_app_2)
    assert "at least 32 characters" in str(exc2.value)

    # 3. Reject debug=True in production
    good_sec = SecuritySettings(
        jwt_secret_key=SecretStr("production-valid-secret-key-32chars!"),
        auth_disabled_dev=False,
    )
    bad_app_3 = Settings(
        app=AppSettings(environment=Environment.PRODUCTION, debug=True),
        security=good_sec,
    )
    with pytest.raises(ValueError) as exc3:
        validate_security_configuration(settings=bad_app_3)
    assert "Debug mode" in str(exc3.value)

    # 4. Valid production settings pass
    valid_app = Settings(
        app=AppSettings(
            environment=Environment.PRODUCTION,
            debug=False,
            cors_origins=["https://app.financial-rag.com"],
        ),
        security=good_sec,
    )
    validate_security_configuration(settings=valid_app)


@pytest.mark.asyncio
async def test_smoke_endpoints_integration(deployment_test_app) -> None:
    """Verify health, version, and security endpoints in deployment configuration."""
    client: AsyncClient = deployment_test_app["client"]

    # Health check
    resp_health = await client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] in ("healthy", "ok", "HEALTHY")

    # Version metadata
    resp_ver = await client.get("/version")
    assert resp_ver.status_code == 200
    ver_data = resp_ver.json()
    assert ver_data["version"] == "1.0.0"
    assert ver_data["git_sha"] == "deploy-test-sha123"

    # Unauthorized access rejection
    resp_unauth = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer invalid.token.str"}
    )
    assert resp_unauth.status_code == 401


def test_graceful_shutdown_configuration() -> None:
    """Verify graceful shutdown timeout and process management settings."""
    settings = Settings()
    assert settings.app.shutdown_timeout_seconds >= 5
    assert settings.app.host == "0.0.0.0"
    assert settings.app.port == 8000
