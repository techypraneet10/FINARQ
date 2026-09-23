"""Privacy-aware redaction utilities for logs and diagnostic payloads."""

import re
from typing import Any

SENSITIVE_KEY_PATTERNS = [
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"api_key", re.IGNORECASE),
    re.compile(r"authorization", re.IGNORECASE),
    re.compile(r"cookie", re.IGNORECASE),
    re.compile(r"bearer", re.IGNORECASE),
]

BEARER_PATTERN = re.compile(r"Bearer\s+([A-Za-z0-9\-_.]+)", re.IGNORECASE)


def redact_sensitive_string(text: str) -> str:
    """Scrub bearer tokens and authorization headers from text strings."""
    if not text:
        return text
    return BEARER_PATTERN.sub("Bearer [REDACTED]", text)


def redact_sensitive_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive keys from dictionaries."""
    sanitized: dict[str, Any] = {}
    for k, v in data.items():
        # Check if key matches sensitive patterns
        is_sensitive = any(pattern.search(k) for pattern in SENSITIVE_KEY_PATTERNS)
        if is_sensitive:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = redact_sensitive_dict(v)
        elif isinstance(v, list):
            sanitized[k] = [
                redact_sensitive_dict(item)
                if isinstance(item, dict)
                else (redact_sensitive_string(item) if isinstance(item, str) else item)
                for item in v
            ]
        elif isinstance(v, str):
            sanitized[k] = redact_sensitive_string(v)
        else:
            sanitized[k] = v
    return sanitized
