"""Liveness probe API endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter, status

from financial_rag.api.dependencies import SettingsDep
from financial_rag.api.v1.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Liveness Probe",
    description="Returns basic health status, application name, version, and current UTC time.",
)
async def get_health(settings: SettingsDep) -> HealthResponse:
    """Liveness probe endpoint."""
    return HealthResponse(
        status="healthy",
        app_name=settings.app.name,
        version=settings.app.version,
        environment=settings.app.environment.value,
        timestamp=datetime.now(UTC),
    )
