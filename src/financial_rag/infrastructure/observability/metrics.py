"""Application metrics registry with low-cardinality enforcement and percentile calculation."""

import math
import threading

from financial_rag.domain.entities.observability import MetricRecord, MetricType
from financial_rag.domain.interfaces.observability import MetricsRegistryProtocol

# Strict whitelist of allowed low-cardinality metric label dimensions
ALLOWED_LABEL_DIMENSIONS = {
    "endpoint",
    "status",
    "provider",
    "model",
    "operation",
    "error_type",
    "error_category",
    "strategy",
    "layer",
    "component",
    "response_style",
    "environment",
    "http_method",
    "tenant_id",
    "circuit_breaker",
    "dependency",
    "type",
    "stage",
    "rule",
    "event_type",
    "state",
    "reason",
    "mode",
    "status_class",
    "attempt",
    "outcome",
    "fallback",
}

# High-cardinality label keys that must NEVER be used in metric dimensions
FORBIDDEN_LABEL_KEYS = {
    "query",
    "text",
    "document_id",
    "user_id",
    "chunk_id",
    "prompt",
    "request_id",
    "trace_id",
    "citation_id",
    "filename",
}


class MetricsRegistry(MetricsRegistryProtocol):
    """Thread-safe in-memory metrics registry supporting Counters, Histograms, and Gauges."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._raw_records: list[MetricRecord] = []

    def _sanitize_labels(self, labels: dict[str, str] | None) -> dict[str, str]:
        """Validate and filter label dimensions against low-cardinality whitelist."""
        if not labels:
            return {}

        sanitized: dict[str, str] = {}
        for k, v in labels.items():
            k_lower = k.lower()
            if k_lower in FORBIDDEN_LABEL_KEYS:
                continue  # Reject high-cardinality label key
            if k_lower in ALLOWED_LABEL_DIMENSIONS:
                sanitized[k_lower] = str(v)[:64]  # Enforce max value length
        return sanitized

    def _make_metric_key(self, name: str, labels: dict[str, str]) -> str:
        """Create deterministic key from name and sorted labels."""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Increment a monotonic counter metric."""
        clean_labels = self._sanitize_labels(labels)
        key = self._make_metric_key(name, clean_labels)

        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value
            self._raw_records.append(
                MetricRecord(
                    name=name,
                    metric_type=MetricType.COUNTER,
                    value=value,
                    labels=clean_labels,
                )
            )

    def record_histogram(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a continuous observation in a histogram metric."""
        clean_labels = self._sanitize_labels(labels)
        key = self._make_metric_key(name, clean_labels)

        with self._lock:
            if key not in self._histograms:
                self._histograms[key] = []
            self._histograms[key].append(value)
            self._raw_records.append(
                MetricRecord(
                    name=name,
                    metric_type=MetricType.HISTOGRAM,
                    value=value,
                    labels=clean_labels,
                )
            )

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        """Set the current value of a gauge metric."""
        clean_labels = self._sanitize_labels(labels)
        key = self._make_metric_key(name, clean_labels)

        with self._lock:
            self._gauges[key] = value
            self._raw_records.append(
                MetricRecord(
                    name=name,
                    metric_type=MetricType.GAUGE,
                    value=value,
                    labels=clean_labels,
                )
            )

    def get_counter_value(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get current counter value."""
        clean_labels = self._sanitize_labels(labels)
        key = self._make_metric_key(name, clean_labels)
        with self._lock:
            return self._counters.get(key, 0.0)

    def get_gauge_value(self, name: str, labels: dict[str, str] | None = None) -> float:
        """Get current gauge value."""
        clean_labels = self._sanitize_labels(labels)
        key = self._make_metric_key(name, clean_labels)
        with self._lock:
            return self._gauges.get(key, 0.0)

    def get_histogram_percentiles(
        self,
        name: str,
        labels: dict[str, str] | None = None,
    ) -> dict[str, float]:
        """Compute P50, P90, P95, P99, mean, min, max, count for histogram metric."""
        clean_labels = self._sanitize_labels(labels)
        key = self._make_metric_key(name, clean_labels)

        with self._lock:
            values = self._histograms.get(key, [])
            if not values:
                return {
                    "count": 0.0,
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p50": 0.0,
                    "p90": 0.0,
                    "p95": 0.0,
                    "p99": 0.0,
                }

            sorted_v = sorted(values)
            n = len(sorted_v)

            def percentile(p: float) -> float:
                idx = math.ceil(p * n) - 1
                return sorted_v[max(0, min(idx, n - 1))]

            return {
                "count": float(n),
                "mean": sum(sorted_v) / float(n),
                "min": sorted_v[0],
                "max": sorted_v[-1],
                "p50": percentile(0.50),
                "p90": percentile(0.90),
                "p95": percentile(0.95),
                "p99": percentile(0.99),
            }

    def format_prometheus(self) -> str:
        """Render all recorded metrics into valid Prometheus text exposition format (version 0.0.4)."""
        lines: list[str] = []

        with self._lock:
            # 1. Format Counters
            counter_groups: dict[str, list[tuple[str, float]]] = {}
            for key, val in sorted(self._counters.items()):
                metric_name = key.split("{")[0]
                if metric_name not in counter_groups:
                    counter_groups[metric_name] = []
                counter_groups[metric_name].append((key, val))

            for metric_name, entries in sorted(counter_groups.items()):
                lines.append(f"# HELP {metric_name} Monotonic counter metric for {metric_name}.")
                lines.append(f"# TYPE {metric_name} counter")
                for key, val in entries:
                    # Format key labels as Prometheus label list
                    if "{" in key:
                        label_str = key[key.index("{") + 1 : -1]
                        prom_labels = ",".join(
                            f'{k}="{v}"'
                            for k, v in [
                                pair.split("=") for pair in label_str.split(",") if "=" in pair
                            ]
                        )
                        lines.append(f"{metric_name}{{{prom_labels}}} {val}")
                    else:
                        lines.append(f"{metric_name} {val}")

            # 2. Format Gauges
            gauge_groups: dict[str, list[tuple[str, float]]] = {}
            for key, val in sorted(self._gauges.items()):
                metric_name = key.split("{")[0]
                if metric_name not in gauge_groups:
                    gauge_groups[metric_name] = []
                gauge_groups[metric_name].append((key, val))

            for metric_name, entries in sorted(gauge_groups.items()):
                lines.append(f"# HELP {metric_name} Current gauge value for {metric_name}.")
                lines.append(f"# TYPE {metric_name} gauge")
                for key, val in entries:
                    if "{" in key:
                        label_str = key[key.index("{") + 1 : -1]
                        prom_labels = ",".join(
                            f'{k}="{v}"'
                            for k, v in [
                                pair.split("=") for pair in label_str.split(",") if "=" in pair
                            ]
                        )
                        lines.append(f"{metric_name}{{{prom_labels}}} {val}")
                    else:
                        lines.append(f"{metric_name} {val}")

            # 3. Format Histograms as Prometheus Quantiles / Summaries
            hist_groups: dict[str, list[tuple[str, list[float]]]] = {}
            for h_key, h_vals in sorted(self._histograms.items()):
                hist_metric_name = h_key.split("{")[0]
                if hist_metric_name not in hist_groups:
                    hist_groups[hist_metric_name] = []
                hist_groups[hist_metric_name].append((h_key, h_vals))

            for hist_name, hist_entries in sorted(hist_groups.items()):
                lines.append(f"# HELP {hist_name} Latency or duration summary for {hist_name}.")
                lines.append(f"# TYPE {hist_name} summary")
                for item_key, item_vals in hist_entries:
                    if not item_vals:
                        continue
                    sorted_v = sorted(item_vals)
                    n = len(sorted_v)

                    def pct(p: float, seq: list[float] = sorted_v, length: int = n) -> float:
                        idx = math.ceil(p * length) - 1
                        return seq[max(0, min(idx, length - 1))]

                    label_prefix = ""
                    if "{" in item_key:
                        raw_labels = item_key[item_key.index("{") + 1 : -1]
                        label_prefix = ",".join(
                            f'{k}="{v}"'
                            for k, v in [
                                pair.split("=") for pair in raw_labels.split(",") if "=" in pair
                            ]
                        )
                        if label_prefix:
                            label_prefix += ","

                    lines.append(f'{hist_name}{{{label_prefix}quantile="0.5"}} {pct(0.5):.4f}')
                    lines.append(f'{hist_name}{{{label_prefix}quantile="0.9"}} {pct(0.9):.4f}')
                    lines.append(f'{hist_name}{{{label_prefix}quantile="0.95"}} {pct(0.95):.4f}')
                    lines.append(f'{hist_name}{{{label_prefix}quantile="0.99"}} {pct(0.99):.4f}')
                    lines.append(
                        f"{hist_name}_sum{{{label_prefix.rstrip(',')}}} {sum(sorted_v):.4f}"
                    )
                    lines.append(f"{hist_name}_count{{{label_prefix.rstrip(',')}}} {float(n)}")

        # Return trailing newline
        return "\n".join(lines) + ("\n" if lines else "")

    def record_llm_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int = 0,
        latency_ms: float = 0.0,
        cost_usd: float = 0.0,
    ) -> None:
        """Record standard LLM inference tokens, latency, and estimated cost."""
        clean_model = model.lower().replace(":", "_")
        self.increment_counter(
            "llm_requests_total", 1.0, labels={"model": clean_model, "status": "success"}
        )
        self.increment_counter(
            "llm_tokens_total", float(input_tokens), labels={"model": clean_model, "type": "input"}
        )
        self.increment_counter(
            "llm_tokens_total",
            float(output_tokens),
            labels={"model": clean_model, "type": "output"},
        )
        if cached_tokens > 0:
            self.increment_counter(
                "llm_tokens_total",
                float(cached_tokens),
                labels={"model": clean_model, "type": "cached"},
            )
        if cost_usd > 0:
            self.increment_counter(
                "llm_cost_estimated_usd_total", float(cost_usd), labels={"model": clean_model}
            )
        if latency_ms > 0:
            self.record_histogram("llm_latency_ms", latency_ms, labels={"model": clean_model})

    def record_circuit_breaker_state(self, component: str, state_value: float) -> None:
        """Record circuit breaker state as gauge (0=CLOSED, 1=HALF_OPEN, 2=OPEN)."""
        self.set_gauge("circuit_breaker_state", state_value, labels={"circuit_breaker": component})

    def record_circuit_breaker_transition(
        self, component: str, from_state: str, to_state: str
    ) -> None:
        """Record circuit breaker state transition."""
        self.increment_counter(
            "circuit_breaker_transitions_total",
            1.0,
            labels={"circuit_breaker": component, "state": to_state},
        )

    def record_circuit_breaker_rejection(self, component: str) -> None:
        """Record fast-failed rejection by open circuit breaker."""
        self.increment_counter(
            "circuit_breaker_rejected_total",
            1.0,
            labels={"circuit_breaker": component},
        )

    def record_ingestion_stage(
        self, stage: str, duration_ms: float, status: str = "success"
    ) -> None:
        """Record timing and counter for document ingestion stages."""
        self.increment_counter(
            "ingestion_stage_total", 1.0, labels={"stage": stage, "status": status}
        )
        if duration_ms > 0:
            self.record_histogram(
                "ingestion_stage_duration_ms",
                duration_ms,
                labels={"stage": stage, "status": status},
            )

    def record_ingestion_latency(self, duration_ms: float, status: str = "success") -> None:
        """Record total document ingestion latency."""
        self.record_histogram("ingestion_latency_ms", duration_ms, labels={"status": status})

    def record_retrieval_metrics(
        self,
        mode: str,
        duration_ms: float,
        candidates_count: int = 0,
        fallback: bool = False,
    ) -> None:
        """Record hybrid, dense, or sparse retrieval latency and counts."""
        status = "fallback" if fallback else "success"
        self.increment_counter(
            "retrieval_requests_total", 1.0, labels={"mode": mode, "status": status}
        )
        if duration_ms > 0:
            self.record_histogram(
                "retrieval_latency_ms", duration_ms, labels={"mode": mode, "status": status}
            )
        if candidates_count > 0:
            self.increment_counter(
                "retrieval_candidates_total", float(candidates_count), labels={"mode": mode}
            )

    def record_rerank_metrics(
        self,
        duration_ms: float,
        candidate_count: int = 0,
        selected_count: int = 0,
        fallback: bool = False,
    ) -> None:
        """Record cross-encoder reranking latency and candidate counts."""
        status = "fallback" if fallback else "success"
        self.increment_counter("rerank_requests_total", 1.0, labels={"status": status})
        if duration_ms > 0:
            self.record_histogram("rerank_latency_ms", duration_ms, labels={"status": status})

    def record_reasoning_metrics(
        self, operation: str, duration_ms: float, status: str = "success"
    ) -> None:
        """Record deterministic financial reasoning timing and operations."""
        self.increment_counter(
            "reasoning_operations_total", 1.0, labels={"operation": operation, "status": status}
        )
        if duration_ms > 0:
            self.record_histogram(
                "reasoning_latency_ms",
                duration_ms,
                labels={"operation": operation, "status": status},
            )

    def record_validation_metrics(self, rule: str, status: str = "success") -> None:
        """Record post-generation answer validation outcomes."""
        self.increment_counter(
            "answer_validation_total", 1.0, labels={"rule": rule, "status": status}
        )

    def record_sse_metrics(
        self,
        event_type: str,
        duration_ms: float = 0.0,
        disconnected: bool = False,
    ) -> None:
        """Record SSE streaming events, duration, and client disconnects."""
        self.increment_counter("sse_events_total", 1.0, labels={"event_type": event_type})
        if duration_ms > 0:
            self.record_histogram(
                "sse_stream_duration_ms", duration_ms, labels={"event_type": event_type}
            )
        if disconnected:
            self.increment_counter(
                "sse_client_disconnects_total", 1.0, labels={"event_type": event_type}
            )

    def record_retry_attempt(
        self,
        component: str,
        attempt: int,
        reason: str = "error",
        status: str = "retrying",
    ) -> None:
        """Record retry invocation for external service or provider."""
        self.increment_counter(
            "retry_attempts_total",
            1.0,
            labels={"component": component, "status": status},
        )

    def record_dependency_check(
        self, dependency: str, duration_ms: float, status: str = "healthy"
    ) -> None:
        """Record health check latency and status for downstream dependencies."""
        if duration_ms > 0:
            self.record_histogram(
                "dependency_latency_ms",
                duration_ms,
                labels={"dependency": dependency, "status": status},
            )

    def get_metrics_snapshot(self) -> list[MetricRecord]:
        """Export raw metrics snapshot."""
        with self._lock:
            return list(self._raw_records)

    def clear(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._raw_records.clear()


# Default singleton metrics registry
metrics_registry = MetricsRegistry()
