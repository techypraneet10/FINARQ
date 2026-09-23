"""Unit tests for standalone IngestionWorkerDaemon."""

import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from financial_rag.common.types import IngestionStage, IngestionStatus
from financial_rag.config.settings import Settings, WorkerSettings
from financial_rag.domain.entities.models import IngestionJob
from financial_rag.worker import IngestionWorkerDaemon


@pytest.fixture
def mock_job_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_pending_jobs = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def mock_ingestion_service() -> MagicMock:
    service = MagicMock()
    service.execute_ingestion_job = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_worker_polls_and_executes_pending_jobs(
    mock_job_repo: MagicMock, mock_ingestion_service: MagicMock
) -> None:
    job1 = IngestionJob(
        id=str(uuid4()),
        document_id=str(uuid4()),
        version_id=str(uuid4()),
        tenant_id="tenant-test",
        status=IngestionStatus.PENDING,
        current_stage=IngestionStage.QUEUED,
        progress_pct=0.0,
        created_at=datetime.now(UTC),
    )

    # First poll returns job1, second returns empty list
    mock_job_repo.get_pending_jobs.side_effect = [[job1], []]

    settings = Settings(
        worker=WorkerSettings(
            concurrency=2,
            poll_interval_seconds=0.01,
            job_timeout_seconds=5,
            batch_size=5,
        )
    )

    worker = IngestionWorkerDaemon(
        settings=settings,
        ingestion_service=mock_ingestion_service,
        job_repo=mock_job_repo,
    )

    # Run worker in background task and stop after brief delay
    task = asyncio.create_task(worker.run())
    await asyncio.sleep(0.05)
    worker.stop()
    await task

    # Assert job was executed
    mock_ingestion_service.execute_ingestion_job.assert_awaited_with(str(job1.id))


@pytest.mark.asyncio
async def test_worker_graceful_shutdown_drains_active_tasks(
    mock_job_repo: MagicMock, mock_ingestion_service: MagicMock
) -> None:
    job = IngestionJob(
        id=str(uuid4()),
        document_id=str(uuid4()),
        version_id=str(uuid4()),
        tenant_id="tenant-test",
        status=IngestionStatus.PENDING,
        current_stage=IngestionStage.QUEUED,
        progress_pct=0.0,
        created_at=datetime.now(UTC),
    )

    mock_job_repo.get_pending_jobs.side_effect = [[job], []]

    async def slow_execution(_job_id: str) -> None:
        await asyncio.sleep(0.03)

    mock_ingestion_service.execute_ingestion_job = AsyncMock(side_effect=slow_execution)

    settings = Settings(
        worker=WorkerSettings(
            concurrency=2,
            poll_interval_seconds=0.01,
            shutdown_timeout_seconds=1.0,
        )
    )

    worker = IngestionWorkerDaemon(
        settings=settings,
        ingestion_service=mock_ingestion_service,
        job_repo=mock_job_repo,
    )

    task = asyncio.create_task(worker.run())
    await asyncio.sleep(0.01)
    worker.stop()
    await task

    mock_ingestion_service.execute_ingestion_job.assert_awaited_once()
