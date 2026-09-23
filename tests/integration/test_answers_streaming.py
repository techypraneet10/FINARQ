"""Integration tests for FastAPI Answer Streaming Endpoint (/api/v1/answers/stream)."""

import json
from collections.abc import AsyncIterator, Generator
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_rag.api.dependencies import get_answer_orchestrator_service
from financial_rag.domain.entities.answer import (
    AnswerRequest,
    AnswerResponse,
    AnswerStatus,
    AnswerStreamEvent,
    AnswerStreamEventType,
)
from financial_rag.domain.entities.reasoning import GroundingStatus
from financial_rag.domain.interfaces.answer import AnswerOrchestratorServiceProtocol
from tests.unit.test_context_builder import make_test_answer_package


class MockStreamingAnswerService(AnswerOrchestratorServiceProtocol):
    """Mock answer service emitting streaming events."""

    async def generate_answer(self, request: AnswerRequest) -> AnswerResponse:
        pkg = make_test_answer_package()
        return AnswerResponse(
            status=AnswerStatus.COMPLETED,
            answer_text="Apple Inc. total net sales for FY2024 was $391,035 million (+2.02%) [C1].",
            claims=pkg.claims,
            citations=pkg.citations,
            calculations=pkg.calculations,
            facts=pkg.facts,
            reasoning_plan=pkg.reasoning_plan,
            grounding_status=GroundingStatus.GROUNDED,
            confidence_score=0.98,
        )

    async def generate_answer_stream(
        self, request: AnswerRequest
    ) -> AsyncIterator[AnswerStreamEvent]:
        seq = 1
        yield AnswerStreamEvent(
            sequence=seq,
            event_type=AnswerStreamEventType.STAGE_START,
            payload={"stage": "reasoning", "query": request.query},
        )
        seq += 1
        yield AnswerStreamEvent(
            sequence=seq,
            event_type=AnswerStreamEventType.REASONING_COMPLETE,
            payload={
                "answerability": "answerable",
                "facts_count": 1,
                "calculations_count": 1,
                "citations_count": 1,
            },
        )
        seq += 1
        yield AnswerStreamEvent(
            sequence=seq,
            event_type=AnswerStreamEventType.CALCULATIONS,
            payload={"calculations": [{"calculation_id": "calc-1", "formula": "grow(2023, 2024)"}]},
        )
        seq += 1
        yield AnswerStreamEvent(
            sequence=seq,
            event_type=AnswerStreamEventType.CITATIONS,
            payload={"citations": [{"citation_id": "cit-1", "page_number": 45}]},
        )
        seq += 1
        tokens = ["Apple ", "reported ", "$391B ", "sales [C1]."]
        for t in tokens:
            yield AnswerStreamEvent(
                sequence=seq,
                event_type=AnswerStreamEventType.TOKEN_DELTA,
                payload={"delta": t},
            )
            seq += 1

        yield AnswerStreamEvent(
            sequence=seq,
            event_type=AnswerStreamEventType.ANSWER_COMPLETE,
            payload={
                "answer_id": str(uuid4()),
                "status": "completed",
                "final_text": "".join(tokens),
            },
        )


@pytest.fixture
def app() -> FastAPI:
    from financial_rag.config.settings import SecuritySettings, Settings
    from financial_rag.main import create_app

    return create_app(settings=Settings(security=SecuritySettings(auth_disabled_dev=True)))


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    mock_service = MockStreamingAnswerService()
    app.dependency_overrides[get_answer_orchestrator_service] = lambda: mock_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_streaming_answer_endpoint_success(client: TestClient) -> None:
    payload = {
        "query": "What was Apple's total net sales in 2024?",
        "response_style": "standard",
        "include_citations": True,
        "top_k": 5,
        "use_reranker": True,
    }
    response = client.post("/api/v1/answers/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    raw_lines = response.text.strip().split("\n\n")
    events = []
    for line in raw_lines:
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    assert len(events) >= 5
    event_types = [e["event_type"] for e in events]
    assert "stage_start" in event_types
    assert "reasoning_complete" in event_types
    assert "calculations" in event_types
    assert "citations" in event_types
    assert "token_delta" in event_types
    assert "answer_complete" in event_types

    deltas = [e["payload"]["delta"] for e in events if e["event_type"] == "token_delta"]
    assert "".join(deltas) == "Apple reported $391B sales [C1]."


def test_streaming_answer_endpoint_validation_error(client: TestClient) -> None:
    # Query too short
    response = client.post("/api/v1/answers/stream", json={"query": "a"})
    assert response.status_code in [400, 422]
