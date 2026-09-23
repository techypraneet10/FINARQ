"""Application service orchestrating document upload, registration, and asynchronous ingestion."""

from datetime import UTC, datetime
from uuid import uuid4

from financial_rag.application.ingestion.hashing import calculate_sha256
from financial_rag.application.ingestion.pipelines import IngestionPipeline
from financial_rag.application.ingestion.validator import DocumentValidator
from financial_rag.common.types import (
    DocumentId,
    DocumentType,
    IngestionStage,
    IngestionStatus,
    JobId,
    VersionId,
)
from financial_rag.domain.entities.models import (
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentVersion,
    IngestionJob,
)
from financial_rag.domain.exceptions import (
    DuplicateDocumentError,
    NotFoundError,
)
from financial_rag.domain.interfaces.repository import (
    ChunkRepositoryProtocol,
    DocumentPageRepositoryProtocol,
    DocumentRepositoryProtocol,
    DocumentVersionRepositoryProtocol,
    IngestionJobRepositoryProtocol,
)
from financial_rag.domain.interfaces.storage import ObjectStorageProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.application.ingestion.service")


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


class DocumentIngestionService:
    """Coordinates document storage, metadata registration, and background processing."""

    def __init__(
        self,
        document_repo: DocumentRepositoryProtocol,
        version_repo: DocumentVersionRepositoryProtocol,
        page_repo: DocumentPageRepositoryProtocol,
        chunk_repo: ChunkRepositoryProtocol,
        job_repo: IngestionJobRepositoryProtocol,
        storage: ObjectStorageProtocol,
        pipeline: IngestionPipeline,
        validator: DocumentValidator | None = None,
    ) -> None:
        self._document_repo = document_repo
        self._version_repo = version_repo
        self._page_repo = page_repo
        self._chunk_repo = chunk_repo
        self._job_repo = job_repo
        self._storage = storage
        self._pipeline = pipeline
        self._validator = validator or DocumentValidator()

    async def upload_and_register_document(
        self,
        content: bytes,
        filename: str,
        document_type: DocumentType = DocumentType.OTHER,
        title: str | None = None,
        ticker_symbol: str | None = None,
        fiscal_year: int | None = None,
        fiscal_period: str | None = None,
        existing_document_id: DocumentId | None = None,
        allow_duplicate: bool = False,
        tenant_id: str = "default_tenant",
        user_id: str | None = None,
    ) -> tuple[Document, DocumentVersion, IngestionJob]:
        """Validate, store binary file, register metadata, and create an ingestion job."""
        # 1. Validation & Filename Sanitization
        safe_filename = self._validator.validate_file(
            content=content,
            filename=filename,
            content_type="application/pdf",
        )

        # 2. Content Hashing & Duplicate Detection
        file_hash = calculate_sha256(content)

        if not allow_duplicate and not existing_document_id:
            existing_doc = await self._document_repo.get_by_hash(file_hash, tenant_id=tenant_id)
            if existing_doc:
                raise DuplicateDocumentError(
                    file_hash=file_hash,
                    existing_document_id=str(existing_doc.id),
                    message=f"Document with identical binary hash already exists (ID: {existing_doc.id}).",
                )

        # 3. Document & Version Identity Generation
        doc_id: DocumentId = existing_document_id or str(uuid4())
        version_id: VersionId = str(uuid4())
        job_id: JobId = str(uuid4())

        # Determine version number
        version_number = 1
        if existing_document_id:
            existing_versions = await self._version_repo.get_by_document_id(
                doc_id, tenant_id=tenant_id
            )
            if existing_versions:
                version_number = max(v.version_number for v in existing_versions) + 1

        # 4. Object Storage Persistence
        storage_key = self._validator.generate_storage_key(
            document_id=str(doc_id),
            version_id=str(version_id),
            filename=safe_filename,
            tenant_id=tenant_id,
        )
        storage_uri = await self._storage.upload(
            key=storage_key,
            data=content,
            content_type="application/pdf",
            metadata={
                "document_id": str(doc_id),
                "version_id": str(version_id),
                "tenant_id": str(tenant_id),
                "filename": safe_filename,
                "file_hash": file_hash,
            },
        )

        # 5. Persist Document & Version in Database
        doc_title = title or safe_filename.replace(".pdf", "").replace("_", " ").title()

        document = Document(
            id=doc_id,
            title=doc_title,
            document_type=document_type,
            tenant_id=tenant_id,
            ticker_symbol=ticker_symbol.upper() if ticker_symbol else None,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            storage_uri=storage_uri,
            file_hash_sha256=file_hash,
            pages_count=0,
            current_version_id=version_id,
            user_id=user_id,
            metadata={"original_filename": filename},
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        persisted_doc = await self._document_repo.save(document)

        version = DocumentVersion(
            id=version_id,
            document_id=doc_id,
            version_number=version_number,
            tenant_id=tenant_id,
            storage_uri=storage_uri,
            file_hash_sha256=file_hash,
            filename=safe_filename,
            file_size_bytes=len(content),
            mime_type="application/pdf",
            pages_count=0,
            created_at=utc_now(),
            metadata={"storage_key": storage_key},
        )
        persisted_version = await self._version_repo.save(version)

        # 6. Create Ingestion Job Record
        job = IngestionJob(
            id=job_id,
            document_id=doc_id,
            version_id=version_id,
            tenant_id=tenant_id,
            user_id=user_id,
            status=IngestionStatus.PENDING,
            current_stage=IngestionStage.QUEUED,
            progress_pct=0.0,
            created_at=utc_now(),
        )
        persisted_job = await self._job_repo.save(job)

        logger.info(
            f"Registered Document {doc_id} (v{version_number}) with IngestionJob {job_id} (tenant={tenant_id})"
        )
        return persisted_doc, persisted_version, persisted_job

    async def execute_ingestion_job(self, job_id: JobId) -> IngestionJob:
        """Execute all processing stages for an ingestion job asynchronously."""
        job = await self._job_repo.get_by_id(job_id)
        if not job:
            raise NotFoundError(resource_type="IngestionJob", resource_id=str(job_id))

        doc = await self._document_repo.get_by_id(job.document_id, tenant_id=job.tenant_id)
        if not doc:
            raise NotFoundError(resource_type="Document", resource_id=str(job.document_id))

        version = await self._version_repo.get_by_id(job.version_id, tenant_id=job.tenant_id)
        if not version:
            raise NotFoundError(resource_type="DocumentVersion", resource_id=str(job.version_id))

        # Update job to PROCESSING
        job.status = IngestionStatus.PROCESSING
        job.started_at = utc_now()
        await self._job_repo.save(job)

        # Extract storage key from metadata or storage URI
        storage_key = version.metadata.get("storage_key")
        if not storage_key:
            storage_key = self._validator.generate_storage_key(
                document_id=str(doc.id),
                version_id=str(version.id),
                filename=version.filename,
                tenant_id=job.tenant_id,
            )

        def _update_stage(stage: IngestionStage, progress: float) -> None:
            job.current_stage = stage
            job.progress_pct = progress

        try:
            # 1. Download file content from object storage
            content = await self._storage.download(storage_key)

            # 2. Run Ingestion Pipeline
            pages, chunks = await self._pipeline.execute(
                content=content,
                document_id=doc.id,
                version_id=version.id,
                document_type=doc.document_type,
                filename=version.filename,
                tenant_id=job.tenant_id,
                on_stage_change=_update_stage,
            )

            # 3. Persist Pages and Chunks in DB
            await self._page_repo.save_batch(pages)
            await self._chunk_repo.save_batch(chunks)

            # 4. Update Document and Version page counts
            doc.pages_count = len(pages)
            doc.updated_at = utc_now()
            await self._document_repo.save(doc)

            version.pages_count = len(pages)
            await self._version_repo.save(version)

            # 5. Mark Job Completed
            job.status = IngestionStatus.COMPLETED
            job.current_stage = IngestionStage.COMPLETED
            job.progress_pct = 100.0
            job.chunks_indexed = len(chunks)
            job.completed_at = utc_now()
            persisted_job = await self._job_repo.save(job)

            logger.info(
                f"IngestionJob {job_id} successfully completed. Indexed {len(chunks)} chunks across {len(pages)} pages."
            )
            return persisted_job

        except Exception as ex:
            logger.error(f"IngestionJob {job_id} failed: {ex}")
            job.status = IngestionStatus.FAILED
            job.error_stage = job.current_stage
            job.current_stage = IngestionStage.FAILED
            job.error_message = str(ex)
            job.error_details = {"exception_type": type(ex).__name__, "error": str(ex)}
            job.completed_at = utc_now()
            return await self._job_repo.save(job)

    async def retry_ingestion_job(
        self, job_id: JobId, tenant_id: str | None = None
    ) -> IngestionJob:
        """Retry a previously failed or pending ingestion job."""
        job = await self._job_repo.get_by_id(job_id, tenant_id=tenant_id)
        if not job:
            raise NotFoundError(resource_type="IngestionJob", resource_id=str(job_id))

        job.status = IngestionStatus.PENDING
        job.current_stage = IngestionStage.QUEUED
        job.progress_pct = 0.0
        job.error_message = None
        job.error_stage = None
        job.error_details = {}
        await self._job_repo.save(job)

        return await self.execute_ingestion_job(job_id)

    async def get_document(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> Document | None:
        return await self._document_repo.get_by_id(document_id, tenant_id=tenant_id)

    async def list_documents(
        self,
        limit: int = 100,
        offset: int = 0,
        ticker_symbol: str | None = None,
        tenant_id: str | None = None,
    ) -> list[Document]:
        return await self._document_repo.list_documents(
            limit=limit, offset=offset, ticker_symbol=ticker_symbol, tenant_id=tenant_id
        )

    async def get_document_versions(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> list[DocumentVersion]:
        return await self._version_repo.get_by_document_id(document_id, tenant_id=tenant_id)

    async def get_document_chunks(
        self, document_id: DocumentId, tenant_id: str | None = None
    ) -> list[DocumentChunk]:
        return await self._chunk_repo.get_by_document_id(document_id, tenant_id=tenant_id)

    async def get_ingestion_job(
        self, job_id: JobId, tenant_id: str | None = None
    ) -> IngestionJob | None:
        return await self._job_repo.get_by_id(job_id, tenant_id=tenant_id)

    async def list_ingestion_jobs(
        self, limit: int = 50, offset: int = 0, tenant_id: str | None = None
    ) -> list[IngestionJob]:
        """List asynchronous ingestion jobs ordered chronologically within tenant."""
        return await self._job_repo.list_jobs(limit=limit, offset=offset, tenant_id=tenant_id)

    async def get_document_pages(
        self,
        document_id: DocumentId,
        version_id: VersionId | None = None,
        tenant_id: str | None = None,
    ) -> list[DocumentPage]:
        """Retrieve extracted document pages for active version or specific version."""
        if not version_id:
            doc = await self._document_repo.get_by_id(document_id, tenant_id=tenant_id)
            if not doc or not doc.current_version_id:
                return []
            version_id = doc.current_version_id
        return await self._page_repo.get_by_version_id(version_id, tenant_id=tenant_id)

    async def get_document_page(
        self, document_id: DocumentId, page_number: int, tenant_id: str | None = None
    ) -> DocumentPage | None:
        """Retrieve a specific document page by page number with bounding boxes."""
        return await self._page_repo.get_by_document_and_page(
            document_id=document_id, page_number=page_number, tenant_id=tenant_id
        )

    async def get_document_binary(
        self,
        document_id: DocumentId,
        version_id: VersionId | None = None,
        tenant_id: str | None = None,
    ) -> bytes | None:
        """Retrieve raw PDF file bytes from object storage."""
        if version_id:
            ver = await self._version_repo.get_by_id(version_id, tenant_id=tenant_id)
            if not ver:
                return None
            storage_uri = ver.storage_uri
        else:
            doc = await self._document_repo.get_by_id(document_id, tenant_id=tenant_id)
            if not doc:
                return None
            storage_uri = doc.storage_uri

        # Extract storage key from uri (e.g. s3://bucket/key or file:///path)
        if storage_uri.startswith("s3://"):
            parts = storage_uri[5:].split("/", 1)
            key = parts[1] if len(parts) > 1 else parts[0]
        elif storage_uri.startswith("file://"):
            key = storage_uri[7:]
        else:
            key = storage_uri

        try:
            return await self._storage.download(key)
        except Exception as ex:
            logger.warning(f"Could not download document binary from {storage_uri}: {ex}")
            return None

    async def delete_document(self, document_id: DocumentId, tenant_id: str | None = None) -> bool:
        """Delete a document, all associated chunks, and remove vectors from vector store."""
        # 1. Check document exists under tenant
        doc = await self._document_repo.get_by_id(document_id, tenant_id=tenant_id)
        if not doc:
            return False

        # 2. Delete vectors from vector store
        try:
            if hasattr(self._pipeline._vector_store, "delete_by_document_id"):
                await self._pipeline._vector_store.delete_by_document_id(
                    str(document_id), tenant_id=tenant_id
                )
        except Exception as ex:
            logger.warning(f"Failed to delete vector embeddings for document {document_id}: {ex}")

        # 3. Delete chunks from DB
        await self._chunk_repo.delete_by_document_id(document_id, tenant_id=tenant_id)

        # 4. Delete document and cascading records from DB
        return await self._document_repo.delete(document_id, tenant_id=tenant_id)
