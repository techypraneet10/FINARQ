"""Phase 10 API Performance & Latency Benchmark Test Suite."""

import statistics
import time
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.api.dependencies import (
    get_answer_orchestrator_service,
    get_reasoning_service,
    get_retrieval_service,
)
from financial_rag.config.settings import SecuritySettings, Settings
from financial_rag.domain.entities.answer import (
    AnswerRequest,
    AnswerResponse,
    AnswerStatus,
    AnswerStreamEvent,
    AnswerStreamEventType,
)
from financial_rag.domain.entities.reasoning import AnswerPackage, GroundingStatus
from financial_rag.domain.entities.retrieval import (
    EvidenceSet,
    FinancialSignals,
    QueryType,
    RetrievalQuery,
)
from financial_rag.domain.interfaces.answer import AnswerOrchestratorServiceProtocol
from financial_rag.domain.interfaces.reasoning import ReasoningServiceProtocol
from financial_rag.domain.interfaces.retrieval import RetrievalServiceProtocol
from financial_rag.main import create_app
from tests.unit.test_context_builder import make_test_answer_package


class BenchmarkMockAnswerService(AnswerOrchestratorServiceProtocol):
    async def generate_answer(self, request: AnswerRequest) -> AnswerResponse:
        pkg = make_test_answer_package()
        return AnswerResponse(
            status=AnswerStatus.COMPLETED,
            answer_text="Apple Inc. reported $391,035 million revenue in FY2024 [C1].",
            claims=pkg.claims,
            citations=pkg.citations,
            calculations=pkg.calculations,
            facts=pkg.facts,
            reasoning_plan=pkg.reasoning_plan,
            grounding_status=GroundingStatus.GROUNDED,
            confidence_score=0.99,
            execution_time_ms={"total_ms": 15.0},
        )

    async def generate_answer_stream(
        self, request: AnswerRequest
    ) -> AsyncIterator[AnswerStreamEvent]:
        yield AnswerStreamEvent(
            sequence=1,
            event_type=AnswerStreamEventType.STAGE_START,
            payload={"stage": "reasoning"},
        )
        yield AnswerStreamEvent(
            sequence=2,
            event_type=AnswerStreamEventType.TOKEN_DELTA,
            payload={"delta": "Apple reported $391B [C1]."},
        )
        yield AnswerStreamEvent(
            sequence=3,
            event_type=AnswerStreamEventType.ANSWER_COMPLETE,
            payload={"status": "completed"},
        )


class BenchmarkMockRetrievalService(RetrievalServiceProtocol):
    async def search(self, *args, **kwargs) -> EvidenceSet:
        signals = FinancialSignals()
        ret_query = RetrievalQuery(
            raw_query="Test query",
            normalized_query="test query",
            query_type=QueryType.FACTUAL,
            signals=signals,
        )
        return EvidenceSet(
            query_id="bench-q1",
            query=ret_query,
            retrieval_strategy="hybrid_dense_sparse",
            items=[],
            total_candidates=0,
            execution_stages=["dense", "sparse", "fusion"],
            timing_ms={"total_ms": 10.0},
        )


class BenchmarkMockReasoningService(ReasoningServiceProtocol):
    async def reason(self, *args, **kwargs) -> AnswerPackage:
        return make_test_answer_package()


@pytest.fixture
def bench_app():
    sec_settings = SecuritySettings(auth_disabled_dev=True)
    app = create_app(settings=Settings(security=sec_settings))
    return app


@pytest.mark.asyncio
async def test_api_latency_benchmarks(bench_app) -> None:
    bench_app.dependency_overrides[get_answer_orchestrator_service] = lambda: (
        BenchmarkMockAnswerService()
    )
    bench_app.dependency_overrides[get_retrieval_service] = lambda: BenchmarkMockRetrievalService()
    bench_app.dependency_overrides[get_reasoning_service] = lambda: BenchmarkMockReasoningService()

    transport = ASGITransport(app=bench_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        iterations = 25

        # 1. Measure Health Latency
        health_latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            resp = await client.get("/health")
            t1 = time.perf_counter()
            assert resp.status_code == 200
            health_latencies.append((t1 - t0) * 1000.0)

        # 2. Measure Search Latency (/api/v1/search)
        search_latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            resp = await client.post(
                "/api/v1/search", json={"query": "What was Apple's net sales in 2024?"}
            )
            t1 = time.perf_counter()
            assert resp.status_code == 200
            search_latencies.append((t1 - t0) * 1000.0)

        # 3. Measure Answer Generation Latency (/api/v1/answers)
        answer_latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            resp = await client.post(
                "/api/v1/answers", json={"query": "What was Apple's net sales in 2024?"}
            )
            t1 = time.perf_counter()
            assert resp.status_code == 200
            answer_latencies.append((t1 - t0) * 1000.0)

        # 4. Measure Stream First-Chunk Latency (/api/v1/answers/stream)
        stream_latencies = []
        for _ in range(iterations):
            t0 = time.perf_counter()
            resp = await client.post(
                "/api/v1/answers/stream", json={"query": "What was Apple's net sales in 2024?"}
            )
            t1 = time.perf_counter()
            assert resp.status_code == 200
            stream_latencies.append((t1 - t0) * 1000.0)

        def calc_metrics(latencies: list[float]) -> dict[str, float]:
            sorted_lat = sorted(latencies)
            p50 = statistics.median(sorted_lat)
            idx95 = max(0, int(len(sorted_lat) * 0.95) - 1)
            idx99 = max(0, int(len(sorted_lat) * 0.99) - 1)
            return {
                "p50": round(p50, 2),
                "p95": round(sorted_lat[idx95], 2),
                "p99": round(sorted_lat[idx99], 2),
            }

        health_metrics = calc_metrics(health_latencies)
        search_metrics = calc_metrics(search_latencies)
        answer_metrics = calc_metrics(answer_latencies)
        stream_metrics = calc_metrics(stream_latencies)

        # Assert performance boundaries (all p95 under 100ms in in-memory test environment)
        assert health_metrics["p95"] < 50.0
        assert search_metrics["p95"] < 100.0
        assert answer_metrics["p95"] < 100.0
        assert stream_metrics["p95"] < 100.0

    bench_app.dependency_overrides.clear()
