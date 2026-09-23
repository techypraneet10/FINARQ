"""Document upload and metadata REST API endpoints with tenant-scoped RBAC."""

from typing import Annotated, Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)

from financial_rag.api.dependencies import (
    AuditServiceDep,
    IngestionServiceDep,
    LoggerDep,
    require_permission,
)
from financial_rag.api.v1.schemas import (
    DocumentChunkResponse,
    DocumentPageResponse,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentVersionResponse,
    FinancialTableCellResponse,
    FinancialTableResponse,
    IngestionJobResponse,
    LayoutBlockResponse,
)
from financial_rag.common.types import DocumentType
from financial_rag.domain.entities.models import DocumentPage
from financial_rag.domain.entities.security import (
    AuditEvent,
    AuditEventType,
    Permission,
    PrincipalContext,
)

router = APIRouter(prefix="/documents", tags=["Documents & Ingestion"])


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload and register a financial document",
    description="Accepts a financial PDF, persists file under tenant key prefix, registers records, and enqueues ingestion.",
)
async def upload_document(
    file: Annotated[UploadFile, File(description="Financial document PDF binary")],
    service: IngestionServiceDep,
    logger: LoggerDep,
    background_tasks: BackgroundTasks,
    audit_service: AuditServiceDep,
    raw_req: Request,
    document_type: Annotated[
        DocumentType, Form(description="Document type category")
    ] = DocumentType.OTHER,
    title: Annotated[str | None, Form(description="Document title (optional)")] = None,
    ticker_symbol: Annotated[
        str | None, Form(description="Stock ticker symbol (e.g. AAPL)")
    ] = None,
    fiscal_year: Annotated[int | None, Form(description="Fiscal year (e.g. 2023)")] = None,
    fiscal_period: Annotated[
        str | None, Form(description="Fiscal period (e.g. Q1, Q2, FY)")
    ] = None,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_WRITE)),
) -> DocumentUploadResponse:
    """Handle document file upload, storage, and asynchronous background ingestion scoped to tenant."""
    filename = file.filename or "uploaded_document.pdf"
    logger.info(
        f"Received document upload request for '{filename}' ({document_type.value}) by user '{principal.user_id}' (tenant='{principal.tenant_id}')"
    )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    # 1. Register document in storage and database strictly scoped to principal's tenant
    doc, version, job = await service.upload_and_register_document(
        content=content,
        filename=filename,
        document_type=document_type,
        title=title,
        ticker_symbol=ticker_symbol,
        fiscal_year=fiscal_year,
        fiscal_period=fiscal_period,
        tenant_id=principal.tenant_id,
        user_id=principal.user_id,
    )

    # 2. Schedule asynchronous background ingestion
    background_tasks.add_task(service.execute_ingestion_job, job.id)

    # 3. Audit log document creation
    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.DOCUMENT_CREATED,
            resource_type="document",
            resource_id=str(doc.id),
            action="upload",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
            metadata={"filename": filename, "version_id": str(version.id)},
        )
    )

    return DocumentUploadResponse(
        document_id=str(doc.id),
        version_id=str(version.id),
        job_id=str(job.id),
        title=doc.title,
        document_type=doc.document_type.value,
        status=job.status.value,
        created_at=job.created_at,
    )


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="List financial documents",
    description="Retrieve paginated list of registered financial documents strictly scoped to caller's tenant.",
)
async def list_documents(
    service: IngestionServiceDep,
    limit: Annotated[int, Query(ge=1, le=200, description="Max documents to return")] = 50,
    offset: Annotated[int, Query(ge=0, description="Pagination offset")] = 0,
    ticker_symbol: Annotated[str | None, Query(description="Filter by ticker symbol")] = None,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> list[DocumentResponse]:
    docs = await service.list_documents(
        limit=limit,
        offset=offset,
        ticker_symbol=ticker_symbol,
        tenant_id=principal.tenant_id,
    )
    return [
        DocumentResponse(
            id=str(d.id),
            title=d.title,
            document_type=d.document_type.value,
            ticker_symbol=d.ticker_symbol,
            fiscal_year=d.fiscal_year,
            fiscal_period=d.fiscal_period,
            storage_uri=d.storage_uri,
            file_hash_sha256=d.file_hash_sha256,
            pages_count=d.pages_count,
            current_version_id=str(d.current_version_id) if d.current_version_id else None,
            metadata=d.metadata,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
    description="Retrieve metadata, page counts, and storage URI for a specific document in caller's tenant.",
)
async def get_document(
    document_id: str,
    service: IngestionServiceDep,
    audit_service: AuditServiceDep,
    raw_req: Request,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> DocumentResponse:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        # Cross-tenant or non-existent document IDOR protection: safe 404
        await audit_service.log_event(
            AuditEvent(
                tenant_id=principal.tenant_id,
                actor_user_id=principal.user_id,
                event_type=AuditEventType.UNAUTHORIZED_ACCESS_ATTEMPT,
                resource_type="document",
                resource_id=document_id,
                action="read",
                outcome="DENIED",
                source_ip=raw_req.client.host if raw_req.client else None,
                user_agent=raw_req.headers.get("user-agent"),
            )
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.DOCUMENT_ACCESSED,
            resource_type="document",
            resource_id=document_id,
            action="read",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    return DocumentResponse(
        id=str(doc.id),
        title=doc.title,
        document_type=doc.document_type.value,
        ticker_symbol=doc.ticker_symbol,
        fiscal_year=doc.fiscal_year,
        fiscal_period=doc.fiscal_period,
        storage_uri=doc.storage_uri,
        file_hash_sha256=doc.file_hash_sha256,
        pages_count=doc.pages_count,
        current_version_id=str(doc.current_version_id) if doc.current_version_id else None,
        metadata=doc.metadata,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a document and all related artifacts",
)
async def delete_document(
    document_id: str,
    service: IngestionServiceDep,
    audit_service: AuditServiceDep,
    raw_req: Request,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_DELETE)),
) -> dict[str, Any]:
    """Delete a document, chunks, and vector index records belonging to caller's tenant."""
    deleted = await service.delete_document(document_id, tenant_id=principal.tenant_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )

    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.DOCUMENT_DELETED,
            resource_type="document",
            resource_id=document_id,
            action="delete",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    return {"message": f"Document '{document_id}' successfully deleted.", "deleted": True}


@router.get(
    "/{document_id}/versions",
    response_model=list[DocumentVersionResponse],
    summary="Get document versions",
    description="Retrieve chronological list of immutable versions for a document.",
)
async def get_document_versions(
    document_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> list[DocumentVersionResponse]:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    versions = await service.get_document_versions(document_id, tenant_id=principal.tenant_id)
    return [
        DocumentVersionResponse(
            id=str(v.id),
            document_id=str(v.document_id),
            version_number=v.version_number,
            storage_uri=v.storage_uri,
            file_hash_sha256=v.file_hash_sha256,
            filename=v.filename,
            file_size_bytes=v.file_size_bytes,
            mime_type=v.mime_type,
            pages_count=v.pages_count,
            created_at=v.created_at,
        )
        for v in versions
    ]


@router.get(
    "/{document_id}/chunks",
    response_model=list[DocumentChunkResponse],
    summary="Get document chunks with provenance",
    description="Retrieve all extracted structure-aware chunks and provenance metadata for a document.",
)
async def get_document_chunks(
    document_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> list[DocumentChunkResponse]:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    chunks = await service.get_document_chunks(document_id, tenant_id=principal.tenant_id)
    return [
        DocumentChunkResponse(
            id=str(c.id),
            document_id=str(c.document_id),
            document_version_id=str(c.document_version_id),
            page_number=c.page_number,
            page_numbers=c.page_numbers or [c.page_number],
            chunk_index=c.chunk_index,
            chunk_type=c.chunk_type.value,
            content=c.content,
            section_path=c.section_path,
            table_id=str(c.table_id) if c.table_id else None,
            token_count=c.token_count,
            char_count=c.char_count,
            source_block_ids=[str(bid) for bid in c.source_block_ids],
            created_at=c.created_at,
        )
        for c in chunks
    ]


@router.get(
    "/jobs/{job_id}",
    response_model=IngestionJobResponse,
    summary="Get ingestion job status",
)
async def get_ingestion_job(
    job_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.INGESTION_READ)),
) -> IngestionJobResponse:
    """Retrieve status and stage of an asynchronous ingestion job within caller's tenant."""
    job = await service.get_ingestion_job(job_id, tenant_id=principal.tenant_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job with ID '{job_id}' not found.",
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
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/jobs/{job_id}/retry",
    response_model=IngestionJobResponse,
    summary="Retry a failed ingestion job",
)
async def retry_ingestion_job(
    job_id: str,
    service: IngestionServiceDep,
    background_tasks: BackgroundTasks,
    audit_service: AuditServiceDep,
    raw_req: Request,
    principal: PrincipalContext = Depends(require_permission(Permission.INGESTION_RETRY)),
) -> IngestionJobResponse:
    """Retry an ingestion job within caller's tenant."""
    job = await service.get_ingestion_job(job_id, tenant_id=principal.tenant_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job with ID '{job_id}' not found.",
        )

    background_tasks.add_task(service.retry_ingestion_job, job_id, principal.tenant_id)

    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.INGESTION_RETRIED,
            resource_type="ingestion_job",
            resource_id=job_id,
            action="retry",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
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
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _map_page_to_response(p: DocumentPage) -> DocumentPageResponse:
    blocks = [
        LayoutBlockResponse(
            id=str(b.id),
            page_number=b.page_number,
            block_type=b.block_type.value if hasattr(b.block_type, "value") else str(b.block_type),
            content=b.content,
            reading_order=b.reading_order,
            bounding_box=b.bounding_box.to_dict() if b.bounding_box else None,
            confidence=b.confidence,
            section_path=b.section_path,
            font_size=b.font_size,
            is_bold=b.is_bold,
            source_method=b.source_method.value
            if hasattr(b.source_method, "value")
            else str(b.source_method),
            metadata=b.metadata,
        )
        for b in p.blocks
    ]
    tables = [
        FinancialTableResponse(
            id=str(t.id),
            page_number=t.page_number,
            title=t.title,
            headers=t.headers,
            rows=t.rows,
            cells=[
                FinancialTableCellResponse(
                    row_idx=c.row_index,
                    col_idx=c.col_index,
                    value=c.text,
                    raw_text=c.raw_text or c.text,
                    is_header=c.is_header,
                    currency=t.currency,
                    scale=t.scale,
                    is_negative=False,
                    is_percentage=False,
                    bounding_box=None,
                )
                for c in t.cells
            ],
            units=t.units,
            currency=t.currency,
            scale=t.scale,
            footnotes=t.footnotes,
            bounding_box=t.bounding_box.to_dict() if t.bounding_box else None,
            markdown_repr=t.markdown_repr,
            csv_repr=t.csv_repr,
            metadata=t.metadata,
        )
        for t in p.tables
    ]
    return DocumentPageResponse(
        id=str(p.id),
        document_id=str(p.document_id),
        version_id=str(p.version_id),
        page_number=p.page_number,
        text_content=p.text_content,
        blocks=blocks,
        tables=tables,
        extraction_method=p.extraction_method.value
        if hasattr(p.extraction_method, "value")
        else str(p.extraction_method),
        has_images=p.has_images,
        confidence=p.confidence,
        width=p.width,
        height=p.height,
        metadata=p.metadata,
    )


@router.get(
    "/{document_id}/pages",
    response_model=list[DocumentPageResponse],
    summary="Get document extracted pages",
    description="Retrieve all extracted pages, layout blocks with bounding boxes, and financial tables for a document.",
)
async def get_document_pages(
    document_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> list[DocumentPageResponse]:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    pages = await service.get_document_pages(document_id, tenant_id=principal.tenant_id)
    return [_map_page_to_response(p) for p in pages]


@router.get(
    "/{document_id}/pages/{page_number}",
    response_model=DocumentPageResponse,
    summary="Get specific document page",
    description="Retrieve single extracted page with bounding boxes and tabular structures.",
)
async def get_document_page(
    document_id: str,
    page_number: int,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> DocumentPageResponse:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    page = await service.get_document_page(
        document_id, page_number=page_number, tenant_id=principal.tenant_id
    )
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} not found for document '{document_id}'.",
        )
    return _map_page_to_response(page)


@router.get(
    "/{document_id}/versions/{version_id}/pages",
    response_model=list[DocumentPageResponse],
    summary="Get version extracted pages",
)
async def get_version_pages(
    document_id: str,
    version_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> list[DocumentPageResponse]:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    pages = await service.get_document_pages(
        document_id, version_id=version_id, tenant_id=principal.tenant_id
    )
    return [_map_page_to_response(p) for p in pages]


@router.get(
    "/{document_id}/file",
    summary="Download or stream document PDF binary",
)
async def download_document_file(
    document_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> Response:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    binary = await service.get_document_binary(document_id, tenant_id=principal.tenant_id)
    if not binary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File binary for document '{document_id}' not found in storage.",
        )
    filename = doc.metadata.get("original_filename", f"{doc.title}.pdf")
    return Response(
        content=binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get(
    "/{document_id}/versions/{version_id}/file",
    summary="Download or stream document version PDF binary",
)
async def download_version_file(
    document_id: str,
    version_id: str,
    service: IngestionServiceDep,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_READ)),
) -> Response:
    doc = await service.get_document(document_id, tenant_id=principal.tenant_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found.",
        )
    binary = await service.get_document_binary(
        document_id, version_id=version_id, tenant_id=principal.tenant_id
    )
    if not binary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File binary for version '{version_id}' not found in storage.",
        )
    return Response(
        content=binary,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="version_{version_id}.pdf"'},
    )
