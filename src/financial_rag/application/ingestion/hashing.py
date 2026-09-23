"""Cryptographic hashing utilities for document content deduplication."""

import hashlib


def calculate_sha256(data: bytes) -> str:
    """Compute standard SHA-256 hexadecimal hash string for binary payload."""
    hasher = hashlib.sha256()
    hasher.update(data)
    return hasher.hexdigest()
