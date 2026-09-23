"""Integration tests for GET /api/v1/metrics endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.main import create_app


@pytest.mark.asyncio
async def test_get_metrics_endpoint() -> None:
    app = create_app()
    # Populate test metrics
    metrics_registry.increment_counter(
        "http_requests_total", 1.0, labels={"endpoint": "/answers", "status": "200"}
    )
    metrics_registry.record_histogram(
        "http_request_duration_ms", 45.2, labels={"endpoint": "/answers"}
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "counters" in data
        assert "gauges" in data
        assert "histograms" in data
        assert "telemetry" in data
        assert "timestamp" in data
        assert "http_request_duration_ms" in data["histograms"]


@pytest.mark.asyncio
async def test_root_metrics_endpoint() -> None:
    """Verify metrics are accessible at root /metrics."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "counters" in data
        assert "gauges" in data
