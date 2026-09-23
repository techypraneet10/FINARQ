from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.observability import (
    DependencyHealthRecord,
    ErrorRecord,
    MetricRecord,
    SpanRecord,
    TraceContext,
)


@runtime_checkable
class SpanProtocol(Protocol):
    """Protocol for an active execution span."""

    @property
    def span_id(self) -> str:
        """Unique span identifier."""
        ...

    @property
    def trace_id(self) -> str:
        """Trace identifier."""
        ...

    def set_attribute(self, key: str, value: Any) -> None:
        """Set span metadata attribute."""
        ...

    def record_error(self, error: Exception | str) -> None:
        """Record an error in the span."""
        ...

    def end(self) -> SpanRecord:
        """Complete the span and record execution duration."""
        ...


@runtime_checkable
class TracerProtocol(Protocol):
    """Protocol for distributed tracing lifecycle."""

    def get_current_context(self) -> TraceContext:
        """Retrieve active trace context."""
        ...

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        parent_span_id: str | None = None,
    ) -> SpanProtocol:
        """Start a new pipeline operation span."""
        ...

    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractContextManager[SpanProtocol]:
        """Synchronous context manager for span lifecycle."""
        ...

    def async_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AbstractAsyncContextManager[SpanProtocol]:
        """Asynchronous context manager for span lifecycle."""
        ...


@runtime_checkable
class MetricsRegistryProtocol(Protocol):
    """Protocol for application metrics management."""

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a counter metric."""
        ...

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a histogram value (e.g. latency, tokens)."""
        ...

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set a gauge metric value."""
        ...

    def get_metrics_snapshot(self) -> list[MetricRecord]:
        """Export all recorded metrics."""
        ...


@runtime_checkable
class CostCalculatorProtocol(Protocol):
    """Protocol for computing LLM token costs."""

    def calculate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
    ) -> float:
        """Calculate estimated cost in USD for token usage."""
        ...


@runtime_checkable
class TelemetryCollectorProtocol(Protocol):
    """Protocol for unified telemetry collection."""

    def record_error(self, error: ErrorRecord) -> None:
        """Record an error event."""
        ...

    def record_fallback(self, component: str, reason: str) -> None:
        """Record a component fallback event."""
        ...

    def record_dependency_health(self, health: DependencyHealthRecord) -> None:
        """Record dependency health check result."""
        ...

    def get_telemetry_snapshot(self) -> dict[str, Any]:
        """Export complete telemetry state."""
        ...
