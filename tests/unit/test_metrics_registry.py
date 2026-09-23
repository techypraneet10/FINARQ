"""Unit tests for MetricsRegistry, percentiles, and label sanitization."""

from financial_rag.infrastructure.observability.metrics import MetricsRegistry


def test_metrics_registry_counter() -> None:
    reg = MetricsRegistry()
    reg.increment_counter("requests_total", 1.0, labels={"endpoint": "/answers", "status": "200"})
    reg.increment_counter("requests_total", 2.0, labels={"endpoint": "/answers", "status": "200"})

    val = reg.get_counter_value("requests_total", labels={"endpoint": "/answers", "status": "200"})
    assert val == 3.0


def test_metrics_registry_histogram_percentiles() -> None:
    reg = MetricsRegistry()
    # Add values 1 to 100
    for v in range(1, 101):
        reg.record_histogram("latency_ms", float(v), labels={"endpoint": "/retrieval"})

    stats = reg.get_histogram_percentiles("latency_ms", labels={"endpoint": "/retrieval"})
    assert stats["count"] == 100.0
    assert stats["min"] == 1.0
    assert stats["max"] == 100.0
    assert stats["p50"] == 50.0
    assert stats["p90"] == 90.0
    assert stats["p95"] == 95.0
    assert stats["p99"] == 99.0


def test_metrics_registry_rejects_high_cardinality_labels() -> None:
    reg = MetricsRegistry()
    # Attempt to inject raw query text and document ID as labels
    reg.increment_counter(
        "query_total",
        1.0,
        labels={
            "endpoint": "/answers",
            "query": "SELECT * FROM secrets",  # Forbidden
            "document_id": "doc-123",  # Forbidden
            "status": "200",  # Allowed
        },
    )

    snapshot = reg.get_metrics_snapshot()
    assert len(snapshot) == 1
    record = snapshot[0]
    assert "query" not in record.labels
    assert "document_id" not in record.labels
    assert record.labels["endpoint"] == "/answers"
    assert record.labels["status"] == "200"
