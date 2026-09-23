"""In-memory auditable answer caching implementation."""

import hashlib
from datetime import UTC, datetime, timedelta

from financial_rag.domain.entities.answer import AnswerRequest, AnswerResponse
from financial_rag.domain.interfaces.answer import AnswerCacheProtocol


class InMemoryAnswerCache(AnswerCacheProtocol):
    """Auditable in-memory cache for validated financial answers."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[AnswerResponse, datetime]] = {}

    async def get(self, cache_key: str) -> AnswerResponse | None:
        """Retrieve unexpired AnswerResponse from cache."""
        if cache_key not in self._store:
            return None

        response, expiry = self._store[cache_key]
        if datetime.now(UTC) > expiry:
            del self._store[cache_key]
            return None

        # Return a copy with cache_hit flag enabled in metadata
        response.metadata["cache_hit"] = True
        return response

    async def set(
        self,
        cache_key: str,
        response: AnswerResponse,
        ttl_seconds: int = 3600,
    ) -> None:
        """Store AnswerResponse in cache with explicit expiration."""
        expiry = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        self._store[cache_key] = (response, expiry)

    def build_cache_key(
        self,
        request: AnswerRequest,
        package_id: str,
        prompt_version: str,
        model_name: str,
    ) -> str:
        """Generate deterministic SHA-256 composite cache key."""
        raw_key = (
            f"query:{request.query.strip().lower()}|"
            f"pkg:{package_id}|"
            f"prompt:{prompt_version}|"
            f"model:{model_name}|"
            f"style:{request.response_style.value}|"
            f"cit:{request.include_citations}"
        )
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def clear(self) -> None:
        """Clear all entries."""
        self._store.clear()
