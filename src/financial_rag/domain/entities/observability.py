"""Domain entities for Phase 5 Observability, Distributed Tracing, Metrics, and Error Taxonomy."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any

from financial_rag.common.types import utc_now


class MetricType(StrEnum):
    """Supported metric semantic types."""

    COUNTER = "counter"
    HISTOGRAM = "histogram"
    GAUGE = "gauge"


class ErrorSeverity(StrEnum):
    """Standardized severity levels for platform errors."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ErrorTaxonomyCategory(StrEnum):
    """Universal error taxonomy across the Financial RAG Platform."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    INGESTION_ERROR = "INGESTION_ERROR"
    RETRIEVAL_ERROR = "RETRIEVAL_ERROR"
    REASONING_ERROR = "REASONING_ERROR"
    CALCULATION_ERROR = "CALCULATION_ERROR"
    CITATION_ERROR = "CITATION_ERROR"
    GROUNDING_ERROR = "GROUNDING_ERROR"
    LLM_ERROR = "LLM_ERROR"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True)
class TraceContext:
    """Distributed tracing correlation context with W3C TraceContext compatibility."""

    trace_id: str
    request_id: str
    parent_span_id: str | None = None
    tenant_id: str | None = None
    trace_flags: str = "01"

    def to_traceparent(self) -> str:
        """Serialize context into standard W3C traceparent header format."""
        raw_trace = self.trace_id.replace("-", "")
        # Pad or truncate to 32 hex chars
        t_hex = raw_trace.rjust(32, "0")[:32]
        raw_span = (self.parent_span_id or "0123456789abcdef").replace("-", "")
        # Pad or truncate to 16 hex chars
        s_hex = raw_span.rjust(16, "0")[:16]
        return f"00-{t_hex}-{s_hex}-{self.trace_flags}"

    @classmethod
    def from_traceparent(
        cls,
        traceparent: str,
        request_id: str | None = None,
        tenant_id: str | None = None,
    ) -> "TraceContext":
        """Parse W3C traceparent header value (version-traceid-parentid-traceflags)."""
        parts = traceparent.strip().split("-")
        if len(parts) >= 4 and parts[0] == "00":
            parsed_trace_id = parts[1]
            parsed_span_id = parts[2]
            parsed_flags = parts[3]
            return cls(
                trace_id=parsed_trace_id,
                request_id=request_id or parsed_trace_id,
                parent_span_id=parsed_span_id,
                tenant_id=tenant_id,
                trace_flags=parsed_flags,
            )
        # Fallback if malformed
        fallback_tid = traceparent.strip() or "00000000000000000000000000000000"
        return cls(
            trace_id=fallback_tid,
            request_id=request_id or fallback_tid,
            parent_span_id=None,
            tenant_id=tenant_id,
            trace_flags="01",
        )


@dataclass
class SpanRecord:
    """An immutable record of an executed pipeline operation span."""

    span_id: str
    trace_id: str
    name: str
    start_time: datetime
    parent_span_id: str | None = None
    end_time: datetime | None = None
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "OK"  # 'OK', 'ERROR', 'UNSET'
    error_message: str | None = None


@dataclass(frozen=True)
class MetricRecord:
    """A point-in-time metric recording."""

    name: str
    metric_type: MetricType
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class ErrorRecord:
    """Standardized error occurrence record."""

    category: ErrorTaxonomyCategory
    code: str
    severity: ErrorSeverity
    recoverable: bool
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None
    request_id: str | None = None
    timestamp: datetime = field(default_factory=utc_now)


@dataclass
class DependencyHealthRecord:
    """Health and fallback availability for external/internal dependencies."""

    dependency_name: str
    is_critical: bool
    status: str  # 'healthy', 'degraded', 'unhealthy'
    details: str = ""
    fallback_available: bool = False
    fallback_active: bool = False
    last_checked_at: datetime = field(default_factory=utc_now)
