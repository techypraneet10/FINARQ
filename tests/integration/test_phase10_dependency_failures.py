"""Phase 10 Dependency Failure Simulation and Graceful Degradation Test Suite."""

import pytest
from httpx import ASGITransport, AsyncClient

from financial_rag.api.dependencies import (
    get_db_session_manager,
    get_embedding,
    get_storage,
    get_vector_database,
)
from financial_rag.config.settings import SecuritySettings, Settings
from financial_rag.domain.entities.models import RetrievalResult
from financial_rag.domain.exceptions import StorageError, VectorStoreError
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.main import create_app


class FailingDBManager:
    async def health_check(self) -> bool:
        return False

    async def close(self) -> None:
        pass


class FailingStorage(ObjectStorageProtocol):
    async def upload(self, *args, **kwargs) -> str:
        raise StorageError("Storage bucket unreachable")

    async def download(self, *args, **kwargs) -> bytes:
        raise StorageError("Storage bucket unreachable")

    async def delete(self, *args, **kwargs) -> bool:
        raise StorageError("Storage bucket unreachable")

    async def exists(self, *args, **kwargs) -> bool:
        raise StorageError("Storage bucket unreachable")

    async def get_metadata(self, *args, **kwargs) -> dict[str, str]:
        raise StorageError("Storage bucket unreachable")

    async def get_presigned_url(self, *args, **kwargs) -> str:
        raise StorageError("Storage bucket unreachable")

    async def health_check(self) -> bool:
        return False


class FailingVectorStore(VectorStoreProtocol):
    async def initialize_collection(self, *args, **kwargs):
        pass

    async def upsert_chunks(self, *args, **kwargs):
        raise VectorStoreError("Qdrant cluster timeout")

    async def search(self, *args, **kwargs) -> list[RetrievalResult]:
        raise VectorStoreError("Qdrant cluster timeout")

    async def delete_by_document_id(self, *args, **kwargs):
        pass

    async def health_check(self) -> bool:
        return False


class HealthyEmbeddingProvider(EmbeddingProviderProtocol):
    @property
    def model_name(self) -> str:
        return "mock"

    @property
    def dimension(self) -> int:
        return 64

    async def embed_text(self, text: str) -> list[float]:
        return [0.1] * 64

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 64 for _ in texts]

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def failure_app():
    sec_settings = SecuritySettings(auth_disabled_dev=True)
    app = create_app(settings=Settings(security=sec_settings))
    return app


@pytest.mark.asyncio
async def test_ready_endpoint_with_degraded_dependencies(failure_app) -> None:
    # Simulate DB down, Vector store down, Storage down
    failure_app.dependency_overrides[get_db_session_manager] = lambda: FailingDBManager()
    failure_app.dependency_overrides[get_storage] = lambda: FailingStorage()
    failure_app.dependency_overrides[get_vector_database] = lambda: FailingVectorStore()
    failure_app.dependency_overrides[get_embedding] = lambda: HealthyEmbeddingProvider()

    transport = ASGITransport(app=failure_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "not_ready"
        assert data["checks"]["database"]["status"] == "unhealthy"
        assert data["checks"]["object_storage"]["status"] == "unhealthy"
        assert data["checks"]["vector_store"]["status"] == "unhealthy"
        assert data["checks"]["embedding_provider"]["status"] == "healthy"

    failure_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_liveness_remains_healthy_during_dependency_outages(failure_app) -> None:
    # Liveness /health should return 200 even when dependencies are down
    transport = ASGITransport(app=failure_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
