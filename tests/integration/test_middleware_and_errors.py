"""Integration tests verifying middleware execution and custom exception handling."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_rag.domain.exceptions import (
    DomainError,
    ExternalServiceError,
    NotFoundError,
)
from financial_rag.domain.exceptions import (
    ValidationError as DomainValidationError,
)


@pytest.mark.integration
def test_custom_request_id_header_propagation(client: TestClient) -> None:
    """Verify inbound X-Request-ID is preserved across request lifecycle."""
    custom_id = "test-custom-request-id-999"
    response = client.get("/health", headers={"X-Request-ID": custom_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == custom_id


@pytest.mark.integration
def test_not_found_exception_handling(app: FastAPI) -> None:
    """Verify NotFoundError is mapped to standard 404 JSON response."""

    @app.get("/test/not-found-trigger")
    async def trigger_not_found() -> None:
        raise NotFoundError(resource_type="SEC_Filing", resource_id="filing-123")

    with TestClient(app) as client:
        response = client.get("/test/not-found-trigger")
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert "filing-123" in data["error"]["message"]
        assert data["error"]["details"]["resource_id"] == "filing-123"


@pytest.mark.integration
def test_domain_error_handling(app: FastAPI) -> None:
    """Verify DomainError is mapped to 400 Bad Request."""

    @app.get("/test/domain-error-trigger")
    async def trigger_domain_error() -> None:
        raise DomainError(message="Fiscal year cannot be in the future")

    with TestClient(app) as client:
        response = client.get("/test/domain-error-trigger")
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "DOMAIN_RULE_VIOLATION"
        assert data["error"]["message"] == "Fiscal year cannot be in the future"


@pytest.mark.integration
def test_domain_validation_error_handling(app: FastAPI) -> None:
    """Verify DomainValidationError is mapped to 422 Unprocessable Entity."""

    @app.get("/test/validation-error-trigger")
    async def trigger_validation_error() -> None:
        raise DomainValidationError(message="Ticker symbol contains invalid characters")

    with TestClient(app) as client:
        response = client.get("/test/validation-error-trigger")
        assert response.status_code == 422
        data = response.json()
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "Ticker symbol" in data["error"]["message"]


@pytest.mark.integration
def test_external_service_error_handling(app: FastAPI) -> None:
    """Verify ExternalServiceError is mapped to 502 Bad Gateway."""

    @app.get("/test/external-error-trigger")
    async def trigger_external_error() -> None:
        raise ExternalServiceError(
            service_name="Qdrant",
            message="Connection refused",
        )

    with TestClient(app) as client:
        response = client.get("/test/external-error-trigger")
        assert response.status_code == 502
        data = response.json()
        assert data["error"]["code"] == "EXTERNAL_SERVICE_ERROR"
        assert "Qdrant" in data["error"]["message"]


@pytest.mark.integration
def test_openapi_schema_endpoint(client: TestClient) -> None:
    """Verify OpenAPI JSON schema generation is functional."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "/health" in schema["paths"]
    assert "/ready" in schema["paths"]
