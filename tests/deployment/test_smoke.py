"""Post-deployment smoke testing verification suite.

Can be run against local test client or a live deployed environment by specifying
the DEPLOY_TARGET_URL environment variable.
"""

import os

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.main import app


@pytest.fixture
def target_base_url() -> str | None:
    return os.environ.get("DEPLOY_TARGET_URL")


@pytest.mark.asyncio
async def test_smoke_health_and_readiness(target_base_url: str | None) -> None:
    """Verify application health and readiness endpoints respond with 200 OK."""
    if target_base_url:
        async with AsyncClient(base_url=target_base_url, timeout=10.0) as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("healthy", "ok", "HEALTHY")

            resp_v1 = await client.get("/api/v1/health")
            assert resp_v1.status_code == 200
    else:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] in ("healthy", "ok", "HEALTHY")

            resp_v1 = await client.get("/api/v1/health")
            assert resp_v1.status_code == 200


@pytest.mark.asyncio
async def test_smoke_version_metadata(target_base_url: str | None) -> None:
    """Verify application version and build metadata are exposed cleanly."""
    if target_base_url:
        async with AsyncClient(base_url=target_base_url, timeout=10.0) as client:
            resp = await client.get("/version")
            assert resp.status_code == 200
            data = resp.json()
            assert "version" in data
            assert "git_sha" in data

            resp_v1 = await client.get("/api/v1/version")
            assert resp_v1.status_code == 200
            data_v1 = resp_v1.json()
            assert "version" in data_v1
            assert "environment" in data_v1
    else:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as client:
            resp = await client.get("/version")
            assert resp.status_code == 200
            data = resp.json()
            assert "version" in data
            assert "git_sha" in data

            resp_v1 = await client.get("/api/v1/version")
            assert resp_v1.status_code == 200
            data_v1 = resp_v1.json()
            assert "version" in data_v1
            assert "environment" in data_v1


@pytest.mark.asyncio
async def test_smoke_security_unauthorized_rejection(target_base_url: str | None) -> None:
    """Verify protected endpoints reject unauthenticated or malformed requests safely."""
    headers = {"Authorization": "Bearer invalid.token.payload"}
    if target_base_url:
        async with AsyncClient(base_url=target_base_url, timeout=10.0) as client:
            resp = await client.get("/api/v1/users/me", headers=headers)
            assert resp.status_code == 401
    else:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=10.0) as client:
            resp = await client.get("/api/v1/users/me", headers=headers)
            assert resp.status_code == 401
