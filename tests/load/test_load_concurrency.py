"""Automated concurrency and stress test suite."""

import pytest
from scripts.load_test import run_load_test


@pytest.mark.asyncio
async def test_high_concurrency_in_memory() -> None:
    """Verify system sustains concurrent requests with zero errors and bounded latency."""
    report = await run_load_test(concurrency=10, requests_per_worker=15)

    assert report["total_requests"] == 150
    assert report["error_count"] == 0
    assert report["error_rate_pct"] == 0.0
    assert report["requests_per_second"] > 10.0
    assert report["latency_p95_ms"] < 200.0
