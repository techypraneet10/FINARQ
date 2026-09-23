"""Global Pytest test configuration and fixtures."""

from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from financial_rag.common.types import Environment
from financial_rag.config.settings import AppSettings, Settings
from financial_rag.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Provide isolated application settings for testing."""
    from financial_rag.config.settings import SecuritySettings

    return Settings(
        app=AppSettings(
            environment=Environment.TESTING,
            name="Financial RAG Test Platform",
            version="0.1.0-test",
            debug=True,
        ),
        security=SecuritySettings(
            auth_disabled_dev=True,
            rate_limit_enabled=False,
        ),
    )


@pytest.fixture
def app(test_settings: Settings) -> FastAPI:
    """Create FastAPI application instance configured for testing."""
    return create_app(settings=test_settings)


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Synchronous HTTP Test Client."""
    with TestClient(app=app, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Asynchronous HTTP Test Client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
