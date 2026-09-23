"""Standalone asynchronous background worker daemon for document ingestion."""

import asyncio
import signal
import sys
from typing import Any

from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.ingestion.service import DocumentIngestionService
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.config.settings import Settings, get_settings
from financial_rag.domain.interfaces.repository import (
    ChunkRepositoryProtocol,
    DocumentPageRepositoryProtocol,
    DocumentRepositoryProtocol,
    DocumentVersionRepositoryProtocol,
    IngestionJobRepositoryProtocol,
)
from financial_rag.infrastructure.chunking.structure_aware import StructureAwareChunker
from financial_rag.infrastructure.embeddings import get_embedding_provider
from financial_rag.infrastructure.logging import (
    clear_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
)
from financial_rag.infrastructure.normalization.document_normalizer import DocumentNormalizer
from financial_rag.infrastructure.observability.error_classifier import ErrorClassifier
from financial_rag.infrastructure.observability.metrics import metrics_registry
from financial_rag.infrastructure.observability.telemetry import telemetry_collector
from financial_rag.infrastructure.parsing.pdf_parser import PyMuPDFParser
from financial_rag.infrastructure.persistence.database import db_manager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresDocumentChunkRepository,
    PostgresDocumentPageRepository,
    PostgresDocumentRepository,
    PostgresDocumentVersionRepository,
    PostgresIngestionJobRepository,
)
from financial_rag.infrastructure.retrieval.sparse_retriever import bm25_retriever
from financial_rag.infrastructure.storage import get_storage_adapter
from financial_rag.infrastructure.structure.detector import FinancialStructureDetector
from financial_rag.infrastructure.table.extractor import FinancialTableExtractor
from financial_rag.infrastructure.table.normalizer import FinancialTableNormalizer
from financial_rag.infrastructure.vector_store import get_vector_store

logger = get_logger("financial_rag.worker")


class IngestionWorkerDaemon:
    """Production asynchronous worker managing concurrent ingestion jobs with bounded backpressure."""

    def __init__(
        self,
        settings: Settings | None = None,
        ingestion_service: DocumentIngestionService | None = None,
        job_repo: IngestionJobRepositoryProtocol | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._job_repo = job_repo or PostgresIngestionJobRepository(session_manager=db_manager)
        self._ingestion_service = ingestion_service
        self._running = False
        self._semaphore = asyncio.Semaphore(self.settings.worker.concurrency)
        self._active_tasks: set[asyncio.Task[Any]] = set()
        self._claimed_job_ids: set[str] = set()

    def _build_default_ingestion_service(self) -> DocumentIngestionService:
        """Construct standard ingestion service with production dependencies."""
        doc_repo: DocumentRepositoryProtocol = PostgresDocumentRepository(
            session_manager=db_manager
        )
        ver_repo: DocumentVersionRepositoryProtocol = PostgresDocumentVersionRepository(
            session_manager=db_manager
        )
        page_repo: DocumentPageRepositoryProtocol = PostgresDocumentPageRepository(
            session_manager=db_manager
        )
        chunk_repo: ChunkRepositoryProtocol = PostgresDocumentChunkRepository(
            session_manager=db_manager
        )

        storage = get_storage_adapter(self.settings.storage)
        embedding = get_embedding_provider(self.settings.embedding)
        vector_store = get_vector_store(self.settings.qdrant)

        table_normalizer = FinancialTableNormalizer()
        pipeline = IngestionPipeline(
            parser=PyMuPDFParser(parser_settings=self.settings.parser),
            table_extractor=FinancialTableExtractor(normalizer=table_normalizer),
            table_normalizer=table_normalizer,
            normalizer=DocumentNormalizer(),
            structure_detector=FinancialStructureDetector(),
            chunker=StructureAwareChunker(chunking_settings=self.settings.chunking),
            embedding_provider=embedding,
            vector_store=vector_store,
            sparse_retriever=bm25_retriever,
        )

        validator = DocumentValidator(settings=self.settings.ingestion)
        return DocumentIngestionService(
            document_repo=doc_repo,
            version_repo=ver_repo,
            page_repo=page_repo,
            chunk_repo=chunk_repo,
            job_repo=self._job_repo,
            storage=storage,
            pipeline=pipeline,
            validator=validator,
        )

    async def _process_job(self, job_id: str, tenant_id: str) -> None:
        """Execute a single claimed ingestion job within bounded semaphore concurrency."""
        async with self._semaphore:
            set_correlation_id(f"job-{job_id}")
            metrics_registry.increment_counter(
                "ingestion_jobs_total", labels={"status": "processing"}
            )
            logger.info(
                f"Worker claimed and started processing IngestionJob {job_id} (tenant={tenant_id})"
            )
            try:
                assert self._ingestion_service is not None
                await asyncio.wait_for(
                    self._ingestion_service.execute_ingestion_job(job_id),
                    timeout=float(self.settings.worker.job_timeout_seconds),
                )
                metrics_registry.increment_counter(
                    "ingestion_jobs_total", labels={"status": "completed"}
                )
                logger.info(f"Worker successfully finished IngestionJob {job_id}")
            except TimeoutError as tex:
                metrics_registry.increment_counter(
                    "ingestion_jobs_total", labels={"status": "failed"}
                )
                err_rec = ErrorClassifier.classify(tex, request_id=f"job-{job_id}")
                telemetry_collector.record_error(err_rec)
                logger.error(
                    f"IngestionJob {job_id} timed out after {self.settings.worker.job_timeout_seconds}s"
                )
            except Exception as ex:
                metrics_registry.increment_counter(
                    "ingestion_jobs_total", labels={"status": "failed"}
                )
                err_rec = ErrorClassifier.classify(ex, request_id=f"job-{job_id}")
                telemetry_collector.record_error(err_rec)
                logger.error(f"Worker error processing IngestionJob {job_id}: {ex}", exc_info=True)
            finally:
                self._claimed_job_ids.discard(job_id)
                clear_correlation_id()

    async def run(self) -> None:
        """Main execution polling loop for background worker."""
        setup_logging(level=self.settings.logging.level, format_type=self.settings.logging.format)
        if self._ingestion_service is None:
            self._ingestion_service = self._build_default_ingestion_service()

        self._running = True
        logger.info(
            f"Starting Financial RAG Ingestion Worker Daemon (concurrency={self.settings.worker.concurrency}, poll_interval={self.settings.worker.poll_interval_seconds}s)"
        )

        while self._running:
            try:
                # Query pending jobs from database
                pending_jobs = await self._job_repo.get_pending_jobs(
                    limit=self.settings.worker.batch_size
                )

                for job in pending_jobs:
                    if not self._running:
                        break
                    job_id_str = str(job.id)
                    if job_id_str in self._claimed_job_ids:
                        continue

                    # Claim job in local tracking
                    self._claimed_job_ids.add(job_id_str)
                    task = asyncio.create_task(self._process_job(job_id_str, str(job.tenant_id)))
                    self._active_tasks.add(task)
                    task.add_done_callback(self._active_tasks.discard)

            except Exception as ex:
                logger.error(f"Error in worker polling loop: {ex}", exc_info=True)

            # Wait before next poll iteration
            try:
                await asyncio.sleep(self.settings.worker.poll_interval_seconds)
            except asyncio.CancelledError:
                break

        logger.info("Worker polling loop exited. Beginning graceful drain of active tasks...")
        await self._drain_tasks()

    async def _drain_tasks(self) -> None:
        """Wait for in-flight tasks to complete within configured shutdown timeout."""
        if not self._active_tasks:
            logger.info("No active ingestion tasks to drain.")
            return

        logger.info(f"Waiting for {len(self._active_tasks)} active ingestion tasks to complete...")
        try:
            await asyncio.wait_for(
                asyncio.gather(*self._active_tasks, return_exceptions=True),
                timeout=self.settings.worker.shutdown_timeout_seconds,
            )
            logger.info("All active ingestion tasks completed successfully.")
        except TimeoutError:
            logger.warning(
                f"Worker shutdown timeout ({self.settings.worker.shutdown_timeout_seconds}s) reached. Cancelling remaining tasks."
            )
            for t in self._active_tasks:
                t.cancel()

    def stop(self) -> None:
        """Signal the worker daemon to stop accepting new jobs and shut down."""
        logger.info("Received shutdown signal. Stopping worker daemon...")
        self._running = False


async def run_worker() -> None:
    """Entrypoint function for starting the worker with OS signal handlers."""
    settings = get_settings()
    worker = IngestionWorkerDaemon(settings=settings)

    loop = asyncio.get_running_loop()

    def _signal_handler() -> None:
        worker.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Signal handlers on Windows loop
            signal.signal(sig, lambda _s, _f: worker.stop())

    try:
        await worker.run()
    finally:
        await db_manager.close()


def main() -> None:
    """CLI script entrypoint."""
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker process exited.")
        sys.exit(0)


if __name__ == "__main__":
    main()
