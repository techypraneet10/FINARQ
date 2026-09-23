"""High-concurrency load and stress testing tool for Financial RAG Platform."""

import argparse
import asyncio
import statistics
import sys
import time
from typing import Any

from httpx import ASGITransport, AsyncClient

from financial_rag.config.settings import get_settings
from financial_rag.infrastructure.logging import get_logger, setup_logging
from financial_rag.main import app

logger = get_logger("financial_rag.scripts.load_test")


async def execute_request(
    client: AsyncClient,
    endpoint: str,
    method: str = "GET",
    json_data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[bool, float, int]:
    """Execute a single HTTP request and record its duration and status code."""
    start_time = time.monotonic()
    try:
        if method == "GET":
            resp = await client.get(endpoint, headers=headers)
        elif method == "POST":
            resp = await client.post(endpoint, json=json_data, headers=headers)
        else:
            resp = await client.request(method, endpoint, headers=headers)

        duration = (time.monotonic() - start_time) * 1000.0  # ms
        is_success = resp.status_code < 400
        return is_success, duration, resp.status_code
    except Exception as ex:
        duration = (time.monotonic() - start_time) * 1000.0
        logger.debug(f"Request failed to {endpoint}: {ex}")
        return False, duration, 0


async def worker_task(
    client: AsyncClient,
    endpoints: list[str],
    requests_per_worker: int,
    results: list[tuple[bool, float, int]],
) -> None:
    """Worker task sending repeated asynchronous requests."""
    for i in range(requests_per_worker):
        endpoint = endpoints[i % len(endpoints)]
        res = await execute_request(client, endpoint)
        results.append(res)


async def run_load_test(
    concurrency: int = 10,
    requests_per_worker: int = 20,
    target_url: str | None = None,
) -> dict[str, Any]:
    """Run concurrent load test against target URL or in-memory ASGI app."""
    endpoints = ["/health", "/version", "/api/v1/health", "/api/v1/version"]
    results: list[tuple[bool, float, int]] = []

    logger.info(
        f"Starting load test with concurrency={concurrency}, requests_per_worker={requests_per_worker} (total={concurrency * requests_per_worker})"
    )

    start_wall_time = time.monotonic()

    if target_url:
        async with AsyncClient(base_url=target_url, timeout=30.0) as client:
            tasks = [
                worker_task(client, endpoints, requests_per_worker, results)
                for _ in range(concurrency)
            ]
            await asyncio.gather(*tasks)
    else:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test", timeout=30.0) as client:
            tasks = [
                worker_task(client, endpoints, requests_per_worker, results)
                for _ in range(concurrency)
            ]
            await asyncio.gather(*tasks)

    total_wall_time = time.monotonic() - start_wall_time

    # Calculate statistics
    total_requests = len(results)
    success_count = sum(1 for success, _, _ in results if success)
    error_count = total_requests - success_count
    latencies = [duration for _, duration, _ in results]

    latencies.sort()
    p50 = statistics.median(latencies) if latencies else 0.0
    p90 = latencies[int(len(latencies) * 0.90)] if latencies else 0.0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0.0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0.0
    rps = total_requests / total_wall_time if total_wall_time > 0 else 0.0

    report = {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "success_count": success_count,
        "error_count": error_count,
        "error_rate_pct": (error_count / total_requests * 100.0) if total_requests else 0.0,
        "total_time_seconds": round(total_wall_time, 3),
        "requests_per_second": round(rps, 2),
        "latency_min_ms": round(min(latencies), 2) if latencies else 0.0,
        "latency_p50_ms": round(p50, 2),
        "latency_p90_ms": round(p90, 2),
        "latency_p95_ms": round(p95, 2),
        "latency_p99_ms": round(p99, 2),
        "latency_max_ms": round(max(latencies), 2) if latencies else 0.0,
    }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Financial RAG Load and Stress Testing Tool")
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Number of concurrent virtual users"
    )
    parser.add_argument("--requests", type=int, default=20, help="Requests per virtual user")
    parser.add_argument(
        "--target-url", type=str, help="Target API URL (defaults to in-memory ASGI app)"
    )
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(level=settings.logging.level, format_type=settings.logging.format)

    report = asyncio.run(run_load_test(args.concurrency, args.requests, args.target_url))

    print("\n" + "=" * 60)
    print("FINANCIAL RAG PLATFORM - LOAD TESTING BENCHMARK REPORT")
    print("=" * 60)
    for k, v in report.items():
        print(f"  {k:<25}: {v}")
    print("=" * 60 + "\n")

    sys.exit(0 if report["error_count"] == 0 else 1)


if __name__ == "__main__":
    main()
