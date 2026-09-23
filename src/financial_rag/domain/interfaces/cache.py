"""Architectural contract for distributed caching and key-value operations."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class CacheProtocol(Protocol):
    """Contract for distributed cache layer (e.g. Redis)."""

    async def get(self, key: str) -> Any | None:
        """Retrieve cached value by key."""
        ...

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> bool:
        """Store value in cache with optional expiration."""
        ...

    async def delete(self, key: str) -> bool:
        """Invalidate key in cache."""
        ...

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        ...

    async def health_check(self) -> bool:
        """Verify cache connectivity health."""
        ...
