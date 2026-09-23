"""Integration tests for Version and Build Metadata APIs."""

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.common.types import Environment
from financial_rag.config.settings import AppSettings, Settings
from financial_rag.main import create_app


@pytest.mark.asyncio
async def test_version_metadata_endpoints() -> None:
    custom_settings = Settings(
        app=AppSettings(
            name="Financial RAG Test Platform",
            version="1.2.3",
            git_sha="abc1234def5678",
            build_timestamp="2026-08-24T12:00:00Z",
            environment=Environment.TESTING,
        )
    )
    app = create_app(settings=custom_settings)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test /api/v1/version
        resp_v1 = await client.get("/api/v1/version")
        assert resp_v1.status_code == 200
        data_v1 = resp_v1.json()
        assert data_v1["application"] == "Financial RAG Test Platform"
        assert data_v1["version"] == "1.2.3"
        assert data_v1["git_sha"] == "abc1234def5678"
        assert data_v1["build_timestamp"] == "2026-08-24T12:00:00Z"
        assert data_v1["environment"] == "testing"
        assert "python_version" in data_v1

        # Test root /version
        resp_root = await client.get("/version")
        assert resp_root.status_code == 200
        data_root = resp_root.json()
        assert data_root["version"] == "1.2.3"
        assert data_root["git_sha"] == "abc1234def5678"
