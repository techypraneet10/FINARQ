"""Unit tests for InMemoryAnswerCache."""

import pytest

from financial_rag.domain.entities.answer import AnswerRequest, AnswerResponse, AnswerStatus
from financial_rag.infrastructure.llm.cache import InMemoryAnswerCache


@pytest.mark.asyncio
async def test_answer_cache_store_and_retrieve() -> None:
    cache = InMemoryAnswerCache()
    req = AnswerRequest(query="What was revenue?")
    key = cache.build_cache_key(req, "pkg-1", "V1", "mock-model")

    resp = AnswerResponse(
        status=AnswerStatus.COMPLETED,
        answer_text="Revenue was $391B [C1]",
    )

    # Initial miss
    assert await cache.get(key) is None

    # Set and retrieve
    await cache.set(key, resp, ttl_seconds=60)
    cached = await cache.get(key)
    assert cached is not None
    assert cached.answer_text == "Revenue was $391B [C1]"
    assert cached.metadata.get("cache_hit") is True


@pytest.mark.asyncio
async def test_answer_cache_expiry() -> None:
    cache = InMemoryAnswerCache()
    req = AnswerRequest(query="What was revenue?")
    key = cache.build_cache_key(req, "pkg-1", "V1", "mock-model")
    resp = AnswerResponse(answer_text="Revenue was $391B")

    # Set with negative TTL (already expired)
    await cache.set(key, resp, ttl_seconds=-1)
    assert await cache.get(key) is None
