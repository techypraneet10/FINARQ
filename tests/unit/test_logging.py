"""Unit tests for structured logging infrastructure."""

import json
import logging

import pytest

from financial_rag.infrastructure.logging import (
    JSONFormatter,
    TextFormatter,
    get_logger,
    request_id_ctx_var,
    setup_logging,
)


@pytest.mark.unit
def test_json_formatter_standard_fields() -> None:
    """Test JSONFormatter generates valid JSON containing all standard keys."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="financial_rag.test",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Processing 10-K filing",
        args=(),
        exc_info=None,
    )

    formatted_str = formatter.format(record)
    data = json.loads(formatted_str)

    assert data["level"] == "INFO"
    assert data["logger"] == "financial_rag.test"
    assert data["message"] == "Processing 10-K filing"
    assert data["line"] == 42
    assert "timestamp" in data


@pytest.mark.unit
def test_json_formatter_with_request_id_context() -> None:
    """Test JSONFormatter includes request_id when present in contextvar."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="financial_rag.api",
        level=logging.WARNING,
        pathname="api.py",
        lineno=100,
        msg="Rate limit approaching",
        args=(),
        exc_info=None,
    )

    token = request_id_ctx_var.set("req-test-uuid-1234")
    try:
        formatted_str = formatter.format(record)
        data = json.loads(formatted_str)
        assert data["request_id"] == "req-test-uuid-1234"
    finally:
        request_id_ctx_var.reset(token)


@pytest.mark.unit
def test_text_formatter_human_readable() -> None:
    """Test TextFormatter outputs clean string with level and logger."""
    formatter = TextFormatter()
    record = logging.LogRecord(
        name="financial_rag.engine",
        level=logging.INFO,
        pathname="engine.py",
        lineno=10,
        msg="Engine ready",
        args=(),
        exc_info=None,
    )

    formatted_str = formatter.format(record)
    assert "[INFO   ]" in formatted_str
    assert "[financial_rag.engine]" in formatted_str
    assert "Engine ready" in formatted_str


@pytest.mark.unit
def test_setup_logging_configures_root_logger() -> None:
    """Test setup_logging sets root logger level and handler."""
    setup_logging(level="DEBUG", format_type="json")
    root_logger = logging.getLogger()

    assert root_logger.level == logging.DEBUG
    assert len(root_logger.handlers) > 0
    assert isinstance(root_logger.handlers[0].formatter, JSONFormatter)


@pytest.mark.unit
def test_get_logger_returns_named_logger() -> None:
    """Test get_logger returns logger with requested module name."""
    logger = get_logger("my.custom.module")
    assert logger.name == "my.custom.module"
