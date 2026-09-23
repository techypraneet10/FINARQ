"""Ingestion job tracking and retry REST API endpoints with tenant isolation."""

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    status,
)

from financial_rag.api.dependencies import (
    IngestionServiceDep,
    LoggerDep,
    require_permission,
)
from financial_rag.api.v1.schemas import IngestionJobResponse
from financial_rag.domain.entities.security import Permission, PrincipalContext

router = APIRouter(prefix="/ingestion-jobs", tags=["Ingestion Jobs"])


@router.get(
    "",
    response_model=list[IngestionJobResponse],
    summary="List ingestion jobs for caller's tenant organization",
    description="Retrieve paginated list of asynchronous ingestion jobs with stage tracking strictly scoped to caller's tenant.",
)
async def list_ingestion_jobs(
    service: IngestionServiceDep,
    limit: int = 50,
    offset: int = 0,
    principal: PrincipalContext = Depends(require_permission(Permission.INGESTION_READ)),
) -> list[IngestionJobResponse]:
    """Retrieve list of ingestion jobs for the authenticated caller's tenant."""
    jobs = await service.list_ingestion_jobs(
        limit=limit, offset=offset, tenant_id=principal.tenant_id
    )
    return [
        IngestionJobResponse(
            id=str(job.id),
            document_id=str(job.document_id),
            version_id=str(job.version_id),
            status=job.status.value,
            current_stage=job.current_stage.value,
            progress_pct=job.progress_pct,
            chunks_indexed=job.chunks_indexed,
            error_message=job.error_message,
            error_stage=job.error_stage.value if job.error_stage else None,
            error_details=job.error_details,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
        for job in jobs
    ]


@router.get(
    "/{job_id}",
    response_model=IngestionJobResponse,
    summary="Get ingestion job status",
    description="Retrieve the real-time processing status, stage, chunk count, and diagnostics for an asynchronous ingestion job scoped to tenant.",
)
async def get_ingestion_job(
    job_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.INGESTION_READ)),
) -> IngestionJobResponse:
    job = await service.get_ingestion_job(job_id, tenant_id=principal.tenant_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IngestionJob with ID '{job_id}' not found.",
        )
    return IngestionJobResponse(
        id=str(job.id),
        document_id=str(job.document_id),
        version_id=str(job.version_id),
        status=job.status.value,
        current_stage=job.current_stage.value,
        progress_pct=job.progress_pct,
        chunks_indexed=job.chunks_indexed,
        error_message=job.error_message,
        error_stage=job.error_stage.value if job.error_stage else None,
        error_details=job.error_details,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/{job_id}/retry",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry a failed ingestion job",
    description="Re-enqueues processing for a previously failed or pending document ingestion job scoped to caller's tenant.",
)
async def retry_ingestion_job(
    job_id: str,
    service: IngestionServiceDep,
    logger: LoggerDep,
    background_tasks: BackgroundTasks,
    principal: PrincipalContext = Depends(require_permission(Permission.INGESTION_RETRY)),
) -> IngestionJobResponse:
    job = await service.get_ingestion_job(job_id, tenant_id=principal.tenant_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IngestionJob with ID '{job_id}' not found.",
        )

    logger.info(
        f"Re-queuing ingestion job {job_id} for retry by user '{principal.user_id}' (tenant='{principal.tenant_id}')"
    )
    # Reset job and trigger execution in background tasks with tenant isolation
    background_tasks.add_task(service.retry_ingestion_job, job_id, principal.tenant_id)

    return IngestionJobResponse(
        id=str(job.id),
        document_id=str(job.document_id),
        version_id=str(job.version_id),
        status="pending",
        current_stage="queued",
        progress_pct=0.0,
        chunks_indexed=job.chunks_indexed,
        error_message=None,
        error_stage=None,
        error_details={},
        created_at=job.created_at,
        started_at=None,
        completed_at=None,
    )
