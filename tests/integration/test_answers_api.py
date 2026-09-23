"""Integration tests for FastAPI Answer Generation Endpoint (/api/v1/answers)."""

from collections.abc import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from financial_rag.api.dependencies import get_answer_orchestrator_service
from financial_rag.domain.entities.answer import (
    AnswerRequest,
    AnswerResponse,
    AnswerStatus,
)
from financial_rag.domain.entities.reasoning import GroundingStatus
from financial_rag.domain.interfaces.answer import AnswerOrchestratorServiceProtocol
from tests.unit.test_context_builder import make_test_answer_package


class MockAnswerService(AnswerOrchestratorServiceProtocol):
    """Mock answer service for API endpoint integration tests."""

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
            warnings=[],
            metadata={"model_name": "mock-llm", "prompt_version": "V1", "attempts": 1},
            execution_time_ms={"total_ms": 42.0},
        )

    async def generate_answer_stream(self, request: AnswerRequest):
        from financial_rag.domain.entities.answer import AnswerStreamEvent, AnswerStreamEventType

        yield AnswerStreamEvent(
            sequence=1,
            event_type=AnswerStreamEventType.TOKEN_DELTA,
            payload={"token": "Apple"},
        )


@pytest.fixture
def app() -> FastAPI:
    from financial_rag.config.settings import SecuritySettings, Settings
    from financial_rag.main import create_app

    return create_app(settings=Settings(security=SecuritySettings(auth_disabled_dev=True)))


@pytest.fixture
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    mock_service = MockAnswerService()
    app.dependency_overrides[get_answer_orchestrator_service] = lambda: mock_service
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_generate_answer_endpoint_success(client: TestClient) -> None:
    payload = {
        "query": "What was Apple's total net sales in 2024?",
        "response_style": "standard",
        "include_citations": True,
        "top_k": 5,
        "use_reranker": True,
    }
    response = client.post("/api/v1/answers", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert "Apple Inc. total net sales" in data["answer"]
    assert len(data["citations"]) == 1
    assert len(data["facts"]) == 1
    assert len(data["calculations"]) == 1
    assert data["metadata"]["model_name"] == "mock-llm"
    assert data["execution_time_ms"]["total_ms"] == 42.0


def test_generate_answer_endpoint_validation_error(client: TestClient) -> None:
    # Query too short (< 2 characters)
    payload = {"query": "x"}
    response = client.post("/api/v1/answers", json=payload)
    assert response.status_code == 422
