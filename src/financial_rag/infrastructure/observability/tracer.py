"""Distributed tracing and pipeline stage span implementation."""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from financial_rag.domain.entities.observability import SpanRecord, TraceContext
from financial_rag.domain.interfaces.observability import SpanProtocol, TracerProtocol

# Context variables for trace and request propagation
trace_id_ctx_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)
current_span_id_ctx_var: ContextVar[str | None] = ContextVar("current_span_id", default=None)
tenant_id_ctx_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)


def set_trace_context(
    trace_id: str | None,
    request_id: str | None = None,
    tenant_id: str | None = None,
) -> None:
    """Explicitly bind active trace and correlation context to async context."""
    trace_id_ctx_var.set(trace_id)
    if request_id is not None:
        request_id_ctx_var.set(request_id)
    if tenant_id is not None:
        tenant_id_ctx_var.set(tenant_id)


def clear_trace_context() -> None:
    """Clear trace and correlation context from current async task."""
    trace_id_ctx_var.set(None)
    request_id_ctx_var.set(None)
    current_span_id_ctx_var.set(None)
    tenant_id_ctx_var.set(None)


class Span(SpanProtocol):
    """An active execution span tracking pipeline timing and metadata."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        self._span_id = str(uuid4())
        self._trace_id = trace_id
        self._parent_span_id = parent_span_id
        self._name = name
        self._start_time = datetime.now(UTC)
        self._end_time: datetime | None = None
        self._duration_ms: float = 0.0
        self._attributes: dict[str, Any] = dict(attributes or {})
        self._status: str = "OK"
        self._error_message: str | None = None

    @property
    def span_id(self) -> str:
        return self._span_id

    @property
    def trace_id(self) -> str:
        return self._trace_id

    @property
    def parent_span_id(self) -> str | None:
        return self._parent_span_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def attributes(self) -> dict[str, Any]:
        return self._attributes

    @property
    def duration_ms(self) -> float:
        return self._duration_ms

    def set_attribute(self, key: str, value: Any) -> None:
        """Set or update span metadata attribute."""
        self._attributes[key] = value

    def record_error(self, error: Exception | str) -> None:
        """Record an error in the span."""
        self._status = "ERROR"
        self._error_message = str(error)
        self.set_attribute("error", True)
        self.set_attribute("error.message", str(error))

    def end(self) -> SpanRecord:
        """Complete the span and record execution duration."""
        if self._end_time is None:
            self._end_time = datetime.now(UTC)
            self._duration_ms = (self._end_time - self._start_time).total_seconds() * 1000.0

        return SpanRecord(
            span_id=self._span_id,
            trace_id=self._trace_id,
            parent_span_id=self._parent_span_id,
            name=self._name,
            start_time=self._start_time,
            end_time=self._end_time,
            duration_ms=self._duration_ms,
            attributes=self._attributes,
            status=self._status,
            error_message=self._error_message,
        )


class Tracer(TracerProtocol):
    """Thread-safe distributed tracer supporting nested spans and context propagation."""

    def __init__(self) -> None:
        self._spans: list[SpanRecord] = []

    def get_current_context(self) -> TraceContext:
        """Retrieve active trace context."""
        t_id = trace_id_ctx_var.get()
        if not t_id:
            t_id = str(uuid4())
            trace_id_ctx_var.set(t_id)

        r_id = request_id_ctx_var.get() or t_id
        parent_id = current_span_id_ctx_var.get()
        tenant_id = tenant_id_ctx_var.get()
        return TraceContext(
            trace_id=t_id,
            request_id=r_id,
            parent_span_id=parent_id,
            tenant_id=tenant_id,
        )

    def start_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
        parent_span_id: str | None = None,
    ) -> Span:
        """Start a new pipeline operation span."""
        ctx = self.get_current_context()
        parent = parent_span_id if parent_span_id is not None else ctx.parent_span_id
        return Span(
            name=name,
            trace_id=ctx.trace_id,
            parent_span_id=parent,
            attributes=attributes,
        )

    @contextmanager
    def span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> Iterator[Span]:
        """Synchronous context manager for span lifecycle."""
        s = self.start_span(name=name, attributes=attributes)
        token = current_span_id_ctx_var.set(s.span_id)
        try:
            yield s
        except Exception as e:
            s.record_error(e)
            raise
        finally:
            record = s.end()
            self._spans.append(record)
            current_span_id_ctx_var.reset(token)

    @asynccontextmanager
    async def async_span(
        self,
        name: str,
        attributes: dict[str, Any] | None = None,
    ) -> AsyncIterator[Span]:
        """Asynchronous context manager for span lifecycle."""
        s = self.start_span(name=name, attributes=attributes)
        token = current_span_id_ctx_var.set(s.span_id)
        try:
            yield s
        except Exception as e:
            s.record_error(e)
            raise
        finally:
            record = s.end()
            self._spans.append(record)
            current_span_id_ctx_var.reset(token)

    def get_recorded_spans(self, trace_id: str | None = None) -> list[SpanRecord]:
        """Retrieve recorded spans, optionally filtered by trace_id."""
        if trace_id:
            return [s for s in self._spans if s.trace_id == trace_id]
        return list(self._spans)

    def clear(self) -> None:
        """Clear recorded spans."""
        self._spans.clear()


# Default singleton tracer instance
tracer = Tracer()
