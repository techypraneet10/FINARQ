"""Structured logging foundation for Financial RAG Platform.

Provides JSON formatted logs in production and structured colored/readable output in development.
Supports context propagation (e.g. request_id, trace_id, tenant_id) via contextvars and sensitive PII/credential redaction.
"""

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Global context variables for request, trace, and tenant tracing
request_id_ctx_var: ContextVar[str | None] = ContextVar("request_id", default=None)
trace_id_ctx_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
tenant_id_ctx_var: ContextVar[str | None] = ContextVar("tenant_id", default=None)

SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "access_token",
    "refresh_token",
    "client_secret",
    "private_key",
}


def redact_sensitive_data(val: Any) -> Any:
    """Recursively mask sensitive values and credentials in logging dictionaries."""
    if isinstance(val, dict):
        redacted: dict[str, Any] = {}
        for k, v in val.items():
            if any(s in k.lower() for s in SENSITIVE_KEYS):
                redacted[k] = "***REDACTED***"
            else:
                redacted[k] = redact_sensitive_data(v)
        return redacted
    elif isinstance(val, list):
        return [redact_sensitive_data(item) for item in val]
    elif isinstance(val, str):
        # Mask bearer tokens and api keys in raw strings
        val = re.sub(r"(?i)bearer\s+[a-zA-Z0-9_\-\.]+", "Bearer ***REDACTED***", val)
        val = re.sub(
            r"(?i)(api[_-]?key|password|secret)\s*[:=\s]\s*['\"]?[^\s,;'\"]+['\"]?",
            r"\1: ***REDACTED***",
            val,
        )
        return val
    return val


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the correlation / request ID for the current async task context."""
    request_id_ctx_var.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear the correlation ID from the current async task context."""
    request_id_ctx_var.set(None)


def get_correlation_id() -> str | None:
    """Retrieve the active correlation ID from the current async task context."""
    return request_id_ctx_var.get()


def bind_context(
    request_id: str | None = None,
    trace_id: str | None = None,
    tenant_id: str | None = None,
) -> None:
    """Convenience helper to bind request, trace, and tenant context variables."""
    if request_id is not None:
        request_id_ctx_var.set(request_id)
    if trace_id is not None:
        trace_id_ctx_var.set(trace_id)
    if tenant_id is not None:
        tenant_id_ctx_var.set(tenant_id)


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects with context and PII redaction."""

    def format(self, record: logging.LogRecord) -> str:
        msg = redact_sensitive_data(record.getMessage())
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": msg,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include request_id, trace_id, tenant_id if available in context
        req_id = request_id_ctx_var.get()
        if req_id:
            log_entry["request_id"] = req_id

        tr_id = trace_id_ctx_var.get()
        if tr_id:
            log_entry["trace_id"] = tr_id

        ten_id = tenant_id_ctx_var.get()
        if ten_id:
            log_entry["tenant_id"] = ten_id

        # Include custom extra fields if provided (redacted)
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_entry["extra"] = redact_sensitive_data(record.extra_fields)

        # Include exception traceback if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable formatted log output for local development with sensitive data redaction."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created, tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
        req_id = request_id_ctx_var.get()
        req_info = f" [{req_id}]" if req_id else ""
        msg = redact_sensitive_data(record.getMessage())
        base = f"[{timestamp}] [{record.levelname:<7}] [{record.name}]{req_info} {msg}"

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)

        return base


def setup_logging(level: str = "INFO", format_type: str = "text") -> None:
    """Initialize root logger configuration."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(numeric_level)

    if format_type.lower() == "json":
        stream_handler.setFormatter(JSONFormatter())
    else:
        stream_handler.setFormatter(TextFormatter())

    root_logger.addHandler(stream_handler)

    # Reduce verbosity of noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Obtain a namespaced logger instance."""
    return logging.getLogger(name)
