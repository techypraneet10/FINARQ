"""Unit tests for Phase 13 Observability, Tracing, Metrics, Redaction, and Resilience."""

import logging

import pytest

from financial_rag.domain.entities.observability import TraceContext
from financial_rag.domain.exceptions import (
    CalculationError,
    DocumentParsingError,
    FileValidationError,
    IncompatibleEmbeddingError,
    InvalidCitationError,
    LLMTimeoutError,
    StorageError,
)
from financial_rag.infrastructure.logging import (
    JSONFormatter,
    bind_context,
    redact_sensitive_data,
)
from financial_rag.infrastructure.observability.cost import CostCalculator
from financial_rag.infrastructure.observability.error_classifier import ErrorClassifier
from financial_rag.infrastructure.observability.metrics import MetricsRegistry
from financial_rag.infrastructure.observability.tracer import Tracer
from financial_rag.infrastructure.resilience.circuit_breaker import (
    CircuitBreakerOpenError,
    CircuitBreakerState,
)
from financial_rag.infrastructure.resilience.registry import CircuitBreakerRegistry


# 1. W3C TraceContext & Distributed Tracing Tests
def test_trace_context_w3c_roundtrip():
    t_id = "4bf92f3577b34da6a3ce929d0e0e4736"
    s_id = "00f067aa0ba902b7"
    raw_header = f"00-{t_id}-{s_id}-01"

    ctx = TraceContext.from_traceparent(raw_header, request_id="req-123", tenant_id="tenant-abc")
    assert ctx.trace_id == t_id
    assert ctx.parent_span_id == s_id
    assert ctx.request_id == "req-123"
    assert ctx.tenant_id == "tenant-abc"
    assert ctx.trace_flags == "01"

    serialized = ctx.to_traceparent()
    assert serialized == raw_header


def test_trace_context_malformed_fallback():
    ctx = TraceContext.from_traceparent("invalid-header-string")
    assert ctx.trace_id == "invalid-header-string"
    assert ctx.parent_span_id is None
    assert len(ctx.to_traceparent()) > 0


def test_tracer_nested_spans():
    tracer = Tracer()
    with tracer.span("parent_op", attributes={"layer": "api"}) as parent:
        parent.set_attribute("attr1", "val1")
        with tracer.span("child_op", attributes={"layer": "retrieval"}) as child:
            child.set_attribute("hits", 10)
            assert child.parent_span_id == parent.span_id
            assert child.trace_id == parent.trace_id

    records = tracer.get_recorded_spans()
    assert len(records) == 2
    child_rec = next(r for r in records if r.name == "child_op")
    parent_rec = next(r for r in records if r.name == "parent_op")
    assert child_rec.attributes["hits"] == 10
    assert parent_rec.attributes["attr1"] == "val1"


# 2. Metrics Registry & Prometheus Exposition Tests
def test_metrics_registry_prometheus_format():
    reg = MetricsRegistry()
    reg.increment_counter(
        "http_requests_total", 5.0, labels={"endpoint": "/api/v1/answers", "status": "200"}
    )
    reg.set_gauge("dependency_up", 1.0, labels={"component": "database", "status": "healthy"})
    for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
        reg.record_histogram("llm_latency_ms", v, labels={"model": "gpt-4o"})

    prom_output = reg.format_prometheus()
    assert "# HELP http_requests_total" in prom_output
    assert "# TYPE http_requests_total counter" in prom_output
    assert 'http_requests_total{endpoint="/api/v1/answers",status="200"} 5.0' in prom_output
    assert "# TYPE dependency_up gauge" in prom_output
    assert 'dependency_up{component="database",status="healthy"} 1.0' in prom_output
    assert "# TYPE llm_latency_ms summary" in prom_output
    assert 'llm_latency_ms{model="gpt-4o",quantile="0.5"} 30.0000' in prom_output


# 3. Sensitive Data Redaction Tests
def test_sensitive_data_redaction():
    sample_payload = {
        "user_email": "analyst@fund.com",
        "password": "SuperSecretPassword123!",
        "auth_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "nested": {
            "api_key": "sk-1234567890abcdef",
            "safe_field": 42,
        },
        "query_text": "Authorization: Bearer my-secret-token-xyz and api_key='secret-123'",
    }

    redacted = redact_sensitive_data(sample_payload)
    assert redacted["user_email"] == "analyst@fund.com"
    assert redacted["password"] == "***REDACTED***"
    assert redacted["auth_token"] == "***REDACTED***"
    assert redacted["nested"]["api_key"] == "***REDACTED***"
    assert redacted["nested"]["safe_field"] == 42
    assert "Bearer ***REDACTED***" in redacted["query_text"]
    assert "api_key" in redacted["query_text"] and "***REDACTED***" in redacted["query_text"]


def test_json_formatter_with_context():
    bind_context(request_id="req-test-99", trace_id="trace-test-99", tenant_id="tenant-hedgefund")
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=100,
        msg="User authenticated with password SecretPass!",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    assert "req-test-99" in formatted
    assert "trace-test-99" in formatted
    assert "tenant-hedgefund" in formatted
    assert "SecretPass!" not in formatted or "***REDACTED***" in formatted


# 4. LLM Cost Calculator Tests
def test_cost_calculator_models():
    calc = CostCalculator()
    # gpt-4o: $2.50 input / 1M, $10.00 output / 1M, $1.25 cached / 1M
    cost_gpt4o = calc.calculate_cost(
        "gpt-4o", input_tokens=1_000_000, output_tokens=100_000, cached_tokens=500_000
    )
    # uncached input: 500k -> $1.25, cached input: 500k -> $0.625, output: 100k -> $1.00 => $2.875
    assert abs(cost_gpt4o - 2.875) < 0.001

    # claude-3-5-sonnet
    cost_claude = calc.calculate_cost(
        "claude-3-5-sonnet-20241022", input_tokens=1_000_000, output_tokens=0
    )
    assert abs(cost_claude - 3.00) < 0.001

    # Free mock model
    cost_mock = calc.calculate_cost("fake-model", input_tokens=500_000, output_tokens=500_000)
    assert cost_mock == 0.0


# 5. Circuit Breaker Registry & State Transitions Tests
@pytest.mark.asyncio
async def test_circuit_breaker_registry_management():
    reg = CircuitBreakerRegistry()
    cb = reg.get_or_create("llm_service", failure_threshold=2, recovery_timeout_seconds=0.1)

    assert cb.state == CircuitBreakerState.CLOSED
    statuses = reg.get_all_statuses()
    assert "llm_service" in statuses
    assert statuses["llm_service"]["state"] == "CLOSED"

    async def fail_call():
        raise RuntimeError("External service 500")

    # Trip breaker
    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.execute(fail_call)

    assert cb.state == CircuitBreakerState.OPEN
    statuses = reg.get_all_statuses()
    assert statuses["llm_service"]["state"] == "OPEN"

    # Fast fail
    with pytest.raises(CircuitBreakerOpenError):
        await cb.execute(fail_call)

    reg.reset_all()
    assert cb.state == CircuitBreakerState.CLOSED


# 6. Error Classifier Tests
def test_error_classifier_categories():
    e1 = ErrorClassifier.classify(FileValidationError("Corrupted PDF header"))
    assert e1.category.value == "VALIDATION_ERROR"
    assert e1.recoverable is True

    e2 = ErrorClassifier.classify(DocumentParsingError("Unreadable scan"))
    assert e2.category.value == "INGESTION_ERROR"
    assert e2.recoverable is False

    e3 = ErrorClassifier.classify(
        IncompatibleEmbeddingError(
            collection_dim=1536,
            query_dim=768,
            collection_name="sec_filings",
        )
    )
    assert e3.category.value == "RETRIEVAL_ERROR"

    e4 = ErrorClassifier.classify(
        CalculationError(operation="growth_rate", message="Negative logarithm")
    )
    assert e4.category.value == "CALCULATION_ERROR"

    e5 = ErrorClassifier.classify(
        InvalidCitationError(citation_id="cit-001", reason="Citation index out of bounds")
    )
    assert e5.category.value == "CITATION_ERROR"

    e6 = ErrorClassifier.classify(LLMTimeoutError(provider="openai", timeout_seconds=30.0))
    assert e6.category.value == "TIMEOUT"

    e7 = ErrorClassifier.classify(StorageError("S3 bucket unreachable"))
    assert e7.category.value == "DEPENDENCY_UNAVAILABLE"
    assert e7.severity.value == "CRITICAL"
