"""Integration tests for Phase 13 Reliability, Telemetry, and Probe Endpoints."""

import pytest
from httpx import AsyncClient

from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.resilience.registry import circuit_breaker_registry


@pytest.mark.asyncio
async def test_metrics_endpoint_content_negotiation(async_client: AsyncClient):
    # Record some test metrics
    metrics_registry.increment_counter(
        "http_requests_total", 3.0, labels={"endpoint": "/api/v1/answers", "status": "200"}
    )
    metrics_registry.record_histogram("retrieval_latency_ms", 12.5, labels={"strategy": "hybrid"})

    # 1. Test JSON format (default)
    json_resp = await async_client.get("/metrics", headers={"Accept": "application/json"})
    assert json_resp.status_code == 200
    data = json_resp.json()
    assert "counters" in data
    assert "gauges" in data
    assert "histograms" in data
    assert "telemetry" in data

    # 2. Test Prometheus text exposition format via Accept header
    prom_resp = await async_client.get("/metrics", headers={"Accept": "text/plain"})
    assert prom_resp.status_code == 200
    assert "text/plain" in prom_resp.headers["content-type"]
    text = prom_resp.text
    assert "# HELP" in text
    assert "# TYPE" in text
    assert "http_requests_total" in text

    # 3. Test Prometheus format via query parameter
    param_resp = await async_client.get("/metrics?format=prometheus")
    assert param_resp.status_code == 200
    assert "text/plain" in param_resp.headers["content-type"]


@pytest.mark.asyncio
async def test_health_and_readiness_probes(async_client: AsyncClient):
    # 1. Liveness probe
    health_resp = await async_client.get("/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["status"] == "healthy"
    assert "app_name" in health_data
    assert "version" in health_data

    # 2. Readiness probe
    ready_resp = await async_client.get("/ready")
    assert ready_resp.status_code == 200
    ready_data = ready_resp.json()
    assert ready_data["status"] in ["ready", "not_ready"]
    checks = ready_data["checks"]
    assert "database" in checks
    assert "object_storage" in checks
    assert "vector_store" in checks
    assert "embedding_provider" in checks
    assert "llm_provider" in checks


@pytest.mark.asyncio
async def test_w3c_correlation_headers_propagation(async_client: AsyncClient):
    req_id = "custom-req-id-9999"
    trace_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    span_id = "00f067aa0ba902b7"
    w3c_header = f"00-{trace_id}-{span_id}-01"

    headers = {
        "X-Request-ID": req_id,
        "traceparent": w3c_header,
    }

    resp = await async_client.get("/health", headers=headers)
    assert resp.status_code == 200
    assert resp.headers["X-Request-ID"] == req_id
    assert resp.headers["X-Trace-ID"] == trace_id
    assert "traceparent" in resp.headers
    assert trace_id in resp.headers["traceparent"]
    assert "X-Process-Time-Ms" in resp.headers


@pytest.mark.asyncio
async def test_circuit_breaker_integration_in_readiness(async_client: AsyncClient):
    # Register and trip a test breaker
    breaker = circuit_breaker_registry.get_or_create("external_market_data", failure_threshold=1)

    async def failing_call():
        raise RuntimeError("Market data vendor timeout")

    with pytest.raises(RuntimeError):
        await breaker.execute(failing_call)

    # Breaker is now OPEN
    assert breaker.state.value == "OPEN"

    ready_resp = await async_client.get("/ready")
    assert ready_resp.status_code == 200
    ready_data = ready_resp.json()
    checks = ready_data["checks"]
    assert "circuit_breaker_external_market_data" in checks
    assert checks["circuit_breaker_external_market_data"]["status"] == "unhealthy"

    # Reset breaker
    breaker.reset()
