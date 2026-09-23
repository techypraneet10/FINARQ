"""Phase 10 Server-Sent Events (SSE) Streaming Resilience, Disconnect & Error Handling Suite."""

import json
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.api.dependencies import get_answer_orchestrator_service
from financial_rag.config.settings import SecuritySettings, Settings
from financial_rag.domain.entities.answer import (
    AnswerRequest,
    AnswerResponse,
    AnswerStatus,
    AnswerStreamEvent,
    AnswerStreamEventType,
)
from financial_rag.domain.entities.reasoning import GroundingStatus
from financial_rag.domain.exceptions import LLMProviderError
from financial_rag.domain.interfaces.answer import AnswerOrchestratorServiceProtocol
from financial_rag.main import create_app
from tests.unit.test_context_builder import make_test_answer_package


class ResilientStreamingMockService(AnswerOrchestratorServiceProtocol):
    """Mock answer service that can simulate success, errors, and long streams."""

    def __init__(self, simulate_error: bool = False):
        self.simulate_error = simulate_error

    async def generate_answer(self, request: AnswerRequest) -> AnswerResponse:
        pkg = make_test_answer_package()
        return AnswerResponse(
            status=AnswerStatus.COMPLETED,
            answer_text="Apple Inc. reported $391,035 million revenue [C1].",
            claims=pkg.claims,
            citations=pkg.citations,
            calculations=pkg.calculations,
            facts=pkg.facts,
            reasoning_plan=pkg.reasoning_plan,
            grounding_status=GroundingStatus.GROUNDED,
            confidence_score=0.99,
        )

    async def generate_answer_stream(
        self, request: AnswerRequest
    ) -> AsyncIterator[AnswerStreamEvent]:
        yield AnswerStreamEvent(
            sequence=1,
            event_type=AnswerStreamEventType.STAGE_START,
            payload={"stage": "reasoning", "query": request.query},
        )
        if self.simulate_error:
            raise LLMProviderError(provider="mock-llm", message="Downstream provider rate limit")

        yield AnswerStreamEvent(
            sequence=2,
            event_type=AnswerStreamEventType.REASONING_COMPLETE,
            payload={"answerability": "answerable", "facts_count": 1},
        )
        yield AnswerStreamEvent(
            sequence=3,
            event_type=AnswerStreamEventType.TOKEN_DELTA,
            payload={"delta": "Apple reported $391B [C1]."},
        )
        yield AnswerStreamEvent(
            sequence=4,
            event_type=AnswerStreamEventType.ANSWER_COMPLETE,
            payload={"status": "completed", "final_text": "Apple reported $391B [C1]."},
        )


@pytest.fixture
def app_with_streaming():
    sec_settings = SecuritySettings(auth_disabled_dev=True)
    app = create_app(settings=Settings(security=sec_settings))
    return app


@pytest.mark.asyncio
async def test_sse_streaming_headers_and_payload_envelope(app_with_streaming) -> None:
    mock_service = ResilientStreamingMockService(simulate_error=False)
    app_with_streaming.dependency_overrides[get_answer_orchestrator_service] = lambda: mock_service

    transport = ASGITransport(app=app_with_streaming)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/answers/stream", json={"query": "What was Apple's FY24 revenue?"}
        )
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert resp.headers["cache-control"] == "no-cache"
        assert resp.headers["x-accel-buffering"] == "no"

        events = []
        for block in resp.text.strip().split("\n\n"):
            if block.startswith("data: "):
                events.append(json.loads(block[6:]))

        assert len(events) == 4
        assert events[0]["event_type"] == "stage_start"
        assert events[1]["event_type"] == "reasoning_complete"
        assert events[2]["event_type"] == "token_delta"
        assert events[3]["event_type"] == "answer_complete"

    app_with_streaming.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_sse_streaming_downstream_error_handling(app_with_streaming) -> None:
    mock_service = ResilientStreamingMockService(simulate_error=True)
    app_with_streaming.dependency_overrides[get_answer_orchestrator_service] = lambda: mock_service

    transport = ASGITransport(app=app_with_streaming)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/answers/stream", json={"query": "What was Apple's revenue?"}
        )
        assert resp.status_code == 200

        events = []
        for block in resp.text.strip().split("\n\n"):
            if block.startswith("data: "):
                events.append(json.loads(block[6:]))

        # First event is stage_start, second event should be a safe error event
        assert len(events) == 2
        assert events[0]["event_type"] == "stage_start"
        assert events[1]["event_type"] == "error"
        assert "STREAM_ERROR" in events[1]["payload"]["code"]

    app_with_streaming.dependency_overrides.clear()
