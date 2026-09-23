"""Operational and application metrics API endpoint."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Header, Query, Request, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.telemetry import telemetry_collector

router = APIRouter(tags=["Observability"])


class MetricsResponse(BaseModel):
    """Operational telemetry and metrics snapshot payload."""

    counters: dict[str, float] = Field(default_factory=dict)
    gauges: dict[str, float] = Field(default_factory=dict)
    histograms: dict[str, dict[str, float]] = Field(default_factory=dict)
    telemetry: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


@router.get(
    "/metrics",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Application & Pipeline Metrics Snapshot",
    description="Exposes in-memory application metrics, histogram percentiles, fallback counts, and error telemetry in JSON or Prometheus exposition format.",
)
async def get_metrics(
    request: Request,
    accept: str | None = Header(default=None),
    format: str | None = Query(default=None),
) -> Response | MetricsResponse:
    """Retrieve current metrics in Prometheus text format or JSON snapshot."""
    wants_prometheus = (format and format.lower() in ("prometheus", "prom", "text")) or (
        accept and "text/plain" in accept.lower()
    )

    if wants_prometheus:
        prom_text = metrics_registry.format_prometheus()
        return PlainTextResponse(
            content=prom_text,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )

    telemetry_state = telemetry_collector.get_telemetry_snapshot()

    # Extract aggregated histogram statistics
    histograms: dict[str, dict[str, float]] = {}
    histograms["http_request_duration_ms"] = metrics_registry.get_histogram_percentiles(
        "http_request_duration_ms"
    )
    histograms["retrieval_latency_ms"] = metrics_registry.get_histogram_percentiles(
        "retrieval_latency_ms"
    )
    histograms["reasoning_latency_ms"] = metrics_registry.get_histogram_percentiles(
        "reasoning_latency_ms"
    )
    histograms["llm_latency_ms"] = metrics_registry.get_histogram_percentiles("llm_latency_ms")

    return MetricsResponse(
        counters=dict(metrics_registry._counters),
        gauges=dict(metrics_registry._gauges),
        histograms=histograms,
        telemetry=telemetry_state,
        timestamp=datetime.now(UTC),
    )
