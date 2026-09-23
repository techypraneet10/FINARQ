import time
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, status

from financial_rag.api.dependencies import (
    SettingsDep,
    get_db_session_manager,
    get_embedding,
    get_storage,
    get_vector_database,
)
from financial_rag.api.v1.schemas import ComponentStatus, ReadyResponse
from financial_rag.domain.entities.observability import DependencyHealthRecord
from financial_rag.domain.interfaces.embedding import EmbeddingProviderProtocol
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.domain.interfaces.vector_store import VectorStoreProtocol
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.telemetry import telemetry_collector
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager

router = APIRouter(tags=["Health"])


@router.get(
    "/ready",
    response_model=ReadyResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Readiness Probe",
    description="Evaluates the operational state of downstream dependencies and adapters.",
)
async def get_readiness(
    settings: SettingsDep,
    db_mgr: Annotated[DatabaseSessionManager, Depends(get_db_session_manager)],
    storage: Annotated[ObjectStorageProtocol, Depends(get_storage)],
    embedding: Annotated[EmbeddingProviderProtocol, Depends(get_embedding)],
    vector_store: Annotated[VectorStoreProtocol, Depends(get_vector_database)],
) -> ReadyResponse:
    """Readiness probe checking real infrastructure health and recording dependency telemetry."""
    t0 = time.perf_counter()
    db_ok = await db_mgr.health_check()
    db_ms = (time.perf_counter() - t0) * 1000.0
    metrics_registry.record_dependency_check("database", db_ms, "healthy" if db_ok else "unhealthy")

    t0 = time.perf_counter()
    storage_ok = await storage.health_check()
    storage_ms = (time.perf_counter() - t0) * 1000.0
    metrics_registry.record_dependency_check(
        "object_storage", storage_ms, "healthy" if storage_ok else "unhealthy"
    )

    t0 = time.perf_counter()
    vector_ok = await vector_store.health_check()
    vector_ms = (time.perf_counter() - t0) * 1000.0
    metrics_registry.record_dependency_check(
        "vector_store", vector_ms, "healthy" if vector_ok else "unhealthy"
    )

    t0 = time.perf_counter()
    embed_ok = await embedding.health_check()
    embed_ms = (time.perf_counter() - t0) * 1000.0
    metrics_registry.record_dependency_check(
        "embedding_provider", embed_ms, "healthy" if embed_ok else "unhealthy"
    )

    # Record dependency health in telemetry aggregator
    telemetry_collector.record_dependency_health(
        DependencyHealthRecord(
            dependency_name="database",
            is_critical=False,
            status="healthy" if db_ok else "unhealthy",
            details="PostgreSQL / SQLite database connection",
            fallback_available=True,
            fallback_active=not db_ok,
        )
    )
    telemetry_collector.record_dependency_health(
        DependencyHealthRecord(
            dependency_name="object_storage",
            is_critical=True,
            status="healthy" if storage_ok else "unhealthy",
            details=f"Storage adapter: {settings.storage.adapter}",
            fallback_available=False,
        )
    )
    telemetry_collector.record_dependency_health(
        DependencyHealthRecord(
            dependency_name="vector_store",
            is_critical=False,
            status="healthy" if vector_ok else "unhealthy",
            details=f"Qdrant vector collection: {settings.qdrant.collection_name}",
            fallback_available=True,  # BM25 sparse fallback available
            fallback_active=not vector_ok,
        )
    )
    telemetry_collector.record_dependency_health(
        DependencyHealthRecord(
            dependency_name="embedding_provider",
            is_critical=True,
            status="healthy" if embed_ok else "unhealthy",
            details=f"Provider: {settings.embedding.provider}, Dim: {settings.embedding.dimension}",
            fallback_available=False,
        )
    )

    checks = {
        "database": ComponentStatus(
            status="healthy" if db_ok else "unhealthy",
            details="Relational database connectivity"
            if db_ok
            else "Database connection failed (degraded mode)",
        ),
        "object_storage": ComponentStatus(
            status="healthy" if storage_ok else "unhealthy",
            details=f"Storage adapter: {settings.storage.adapter}",
        ),
        "vector_store": ComponentStatus(
            status="healthy" if vector_ok else "unhealthy",
            details=f"Qdrant collection: {settings.qdrant.collection_name}"
            if vector_ok
            else "Qdrant unavailable (BM25 sparse fallback active)",
        ),
        "embedding_provider": ComponentStatus(
            status="healthy" if embed_ok else "unhealthy",
            details=f"Provider: {settings.embedding.provider}, Dim: {settings.embedding.dimension}",
        ),
        "llm_provider": ComponentStatus(
            status="configured",
            details=f"Provider: {settings.llm.provider}, Model: {settings.llm.model_name}",
        ),
    }

    # Check circuit breakers
    from financial_rag.infrastructure.resilience.registry import circuit_breaker_registry

    cb_statuses = circuit_breaker_registry.get_all_statuses()
    for cb_name, cb_info in cb_statuses.items():
        state_str = cb_info["state"]
        checks[f"circuit_breaker_{cb_name}"] = ComponentStatus(
            status="healthy"
            if state_str == "CLOSED"
            else ("degraded" if state_str == "HALF_OPEN" else "unhealthy"),
            details=f"State: {state_str}, Failures: {cb_info['failure_count']}/{cb_info['failure_threshold']}",
        )

    # Service reports ready if critical storage and embedding dependencies are functional
    is_ready = storage_ok and embed_ok

    return ReadyResponse(
        status="ready" if is_ready else "not_ready",
        checks=checks,
        timestamp=datetime.now(UTC),
    )
