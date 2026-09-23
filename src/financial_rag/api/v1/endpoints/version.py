import sys

from fastapi import APIRouter, status

from financial_rag.api.dependencies import SettingsDep
from financial_rag.api.v1.schemas import VersionResponse

router = APIRouter(tags=["Metadata"])


@router.get(
    "/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Application Version and Build Metadata",
    description="Returns safe runtime build metadata, Git SHA, and environment information without leaking internal secrets.",
)
async def get_version(
    settings: SettingsDep,
) -> VersionResponse:
    """Return safe build and version metadata for observability and deployment audits."""
    return VersionResponse(
        application=settings.app.name,
        version=settings.app.version,
        git_sha=settings.app.git_sha,
        build_timestamp=settings.app.build_timestamp,
        environment=settings.app.environment.value,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    )
