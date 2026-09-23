"""Unified telemetry collector aggregating errors, fallbacks, and dependency health."""

import threading
from typing import Any

from financial_rag.domain.entities.observability import DependencyHealthRecord, ErrorRecord
from financial_rag.domain.interfaces.observability import TelemetryCollectorProtocol
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.tracer import tracer


class TelemetryCollector(TelemetryCollectorProtocol):
    """Centralized telemetry aggregator tracking system reliability, errors, and fallbacks."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._errors: list[ErrorRecord] = []
        self._fallbacks: list[dict[str, Any]] = []
        self._dependency_health: dict[str, DependencyHealthRecord] = {}

    def record_error(self, error: ErrorRecord) -> None:
        """Record an error event and update corresponding error counter metric."""
        with self._lock:
            self._errors.append(error)
            # Keep bounded in-memory buffer
            if len(self._errors) > 1000:
                self._errors = self._errors[-1000:]

        metrics_registry.increment_counter(
            name="error_total",
            labels={
                "error_type": error.category.value,
                "status": "error",
            },
        )

    def record_fallback(self, component: str, reason: str) -> None:
        """Record a component fallback event and update fallback counter metric."""
        with self._lock:
            self._fallbacks.append({"component": component, "reason": reason})
            if len(self._fallbacks) > 1000:
                self._fallbacks = self._fallbacks[-1000:]

        metrics_registry.increment_counter(
            name="fallback_total",
            labels={
                "component": component,
                "status": "fallback",
            },
        )

    def record_dependency_health(self, health: DependencyHealthRecord) -> None:
        """Record health check result for a dependency."""
        with self._lock:
            self._dependency_health[health.dependency_name] = health

        metrics_registry.set_gauge(
            name="dependency_up",
            value=1.0
            if health.status == "healthy"
            else (0.5 if health.status == "degraded" else 0.0),
            labels={
                "component": health.dependency_name,
                "status": health.status,
            },
        )

    def get_telemetry_snapshot(self) -> dict[str, Any]:
        """Export comprehensive telemetry state."""
        with self._lock:
            return {
                "total_errors_recorded": len(self._errors),
                "total_fallbacks_recorded": len(self._fallbacks),
                "recent_errors": [
                    {
                        "category": e.category.value,
                        "code": e.code,
                        "severity": e.severity.value,
                        "recoverable": e.recoverable,
                        "message": e.message,
                        "timestamp": e.timestamp.isoformat(),
                    }
                    for e in self._errors[-20:]
                ],
                "recent_fallbacks": list(self._fallbacks[-20:]),
                "dependency_health": {
                    k: {
                        "status": v.status,
                        "is_critical": v.is_critical,
                        "details": v.details,
                        "fallback_available": v.fallback_available,
                        "fallback_active": v.fallback_active,
                        "last_checked_at": v.last_checked_at.isoformat(),
                    }
                    for k, v in self._dependency_health.items()
                },
                "total_spans_recorded": len(tracer.get_recorded_spans()),
            }

    def clear(self) -> None:
        """Clear telemetry buffer."""
        with self._lock:
            self._errors.clear()
            self._fallbacks.clear()
            self._dependency_health.clear()


# Default singleton telemetry collector
telemetry_collector = TelemetryCollector()
