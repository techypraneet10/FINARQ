"""Integration tests for application health endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_health_endpoint(client: TestClient) -> None:
    """Test GET /health returns 200 OK and expected schema."""
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "Financial RAG Test Platform"
    assert data["version"] == "0.1.0-test"
    assert data["environment"] == "testing"
    assert "timestamp" in data

    # Middleware header checks
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time-Ms" in response.headers


@pytest.mark.integration
def test_versioned_health_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/health returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0-test"
