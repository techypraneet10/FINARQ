"""Integration tests for application readiness endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_root_ready_endpoint(client: TestClient) -> None:
    """Test GET /ready returns 200 OK and subsystem check results."""
    response = client.get("/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data
    assert "timestamp" in data

    checks = data["checks"]
    assert "database" in checks
    assert "vector_store" in checks
    assert "object_storage" in checks
    assert "llm_provider" in checks
    assert "embedding_provider" in checks


@pytest.mark.integration
def test_versioned_ready_endpoint(client: TestClient) -> None:
    """Test GET /api/v1/ready returns 200 OK."""
    response = client.get("/api/v1/ready")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["ready", "not_ready"]
    assert "checks" in data
