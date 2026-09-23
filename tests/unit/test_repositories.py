"""Unit tests for relational persistence repositories using async SQLite engine."""

from uuid import uuid4

import pytest

from financial_rag.common.types import (
    BlockType,
    ChunkType,
    DocumentType,
    IngestionStage,
    IngestionStatus,
)
from financial_rag.config.settings import DatabaseSettings
from financial_rag.domain.entities.models import (
    Document,
    DocumentChunk,
    DocumentPage,
    DocumentVersion,
    FinancialTable,
    IngestionJob,
    LayoutBlock,
)
from financial_rag.domain.entities.value_objects import BoundingBox
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresDocumentChunkRepository,
    PostgresDocumentPageRepository,
    PostgresDocumentRepository,
    PostgresDocumentVersionRepository,
    PostgresIngestionJobRepository,
)


@pytest.fixture
async def session_mgr(tmp_path):
    db_file = tmp_path / "test_rag.db"
    settings = DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}")
    mgr = DatabaseSessionManager(db_settings=settings)
    await mgr.create_all_tables()
    yield mgr
    await mgr.close()


@pytest.mark.unit
async def test_document_repository_crud(session_mgr) -> None:
    repo = PostgresDocumentRepository(session_manager=session_mgr)
    doc_id = str(uuid4())

    doc = Document(
        id=doc_id,
        title="Apple Inc. 10-K FY2023",
        document_type=DocumentType.SEC_10K,
        ticker_symbol="AAPL",
        fiscal_year=2023,
        fiscal_period="FY",
        storage_uri="s3://financial-documents/aapl.pdf",
        file_hash_sha256="abc123hash",
        pages_count=85,
    )

    # Save
    saved = await repo.save(doc)
    assert saved.id == doc_id
    assert saved.ticker_symbol == "AAPL"

    # Get by ID
    fetched = await repo.get_by_id(doc_id)
    assert fetched is not None
    assert fetched.title == "Apple Inc. 10-K FY2023"

    # Get by Hash
    by_hash = await repo.get_by_hash("abc123hash")
    assert by_hash is not None
    assert by_hash.id == doc_id

    # List
    doc_list = await repo.list_documents(ticker_symbol="AAPL")
    assert len(doc_list) == 1

    # Delete
    assert await repo.delete(doc_id) is True
    assert await repo.get_by_id(doc_id) is None


@pytest.mark.unit
async def test_version_page_chunk_repositories(session_mgr) -> None:
    doc_repo = PostgresDocumentRepository(session_manager=session_mgr)
    ver_repo = PostgresDocumentVersionRepository(session_manager=session_mgr)
    page_repo = PostgresDocumentPageRepository(session_manager=session_mgr)
    chunk_repo = PostgresDocumentChunkRepository(session_manager=session_mgr)
    job_repo = PostgresIngestionJobRepository(session_manager=session_mgr)

    doc_id = str(uuid4())
    version_id = str(uuid4())

    # Parent Document
    await doc_repo.save(
        Document(
            id=doc_id,
            title="Microsoft 10-Q Q1 2024",
            document_type=DocumentType.SEC_10Q,
            ticker_symbol="MSFT",
            storage_uri="documents/msft.pdf",
            file_hash_sha256="msft123",
        )
    )

    # Document Version
    version = DocumentVersion(
        id=version_id,
        document_id=doc_id,
        version_number=1,
        storage_uri="documents/msft_v1.pdf",
        file_hash_sha256="msft123",
        filename="msft.pdf",
        file_size_bytes=1024,
        pages_count=2,
    )
    await ver_repo.save(version)

    # Document Page
    page1 = DocumentPage(
        id=str(uuid4()),
        document_id=doc_id,
        version_id=version_id,
        page_number=1,
        text_content="Page 1 narrative content",
        blocks=[
            LayoutBlock(
                id=str(uuid4()),
                page_number=1,
                block_type=BlockType.HEADING,
                content="Heading block",
                bounding_box=BoundingBox(50, 50, 500, 70),
            )
        ],
        tables=[
            FinancialTable(
                id=str(uuid4()),
                page_number=1,
                title="Balance Sheet",
                headers=["Asset", "2023"],
                rows=[["Cash", "$100"]],
            )
        ],
    )
    await page_repo.save_batch([page1])
    pages = await page_repo.get_by_version_id(version_id)
    assert len(pages) == 1
    assert len(pages[0].blocks) == 1
    assert len(pages[0].tables) == 1

    # Document Chunks
    chunk1 = DocumentChunk(
        id=str(uuid4()),
        document_id=doc_id,
        document_version_id=version_id,
        page_number=1,
        chunk_index=0,
        chunk_type=ChunkType.TEXT,
        content="Chunk 1 content",
        section_path="Part I > Item 1",
    )
    await chunk_repo.save_batch([chunk1])
    chunks = await chunk_repo.get_by_document_id(doc_id)
    assert len(chunks) == 1
    assert chunks[0].section_path == "Part I > Item 1"

    # Ingestion Job
    job_id = str(uuid4())
    job = IngestionJob(
        id=job_id,
        document_id=doc_id,
        version_id=version_id,
        status=IngestionStatus.PROCESSING,
        current_stage=IngestionStage.CHUNKING,
        progress_pct=55.0,
    )
    await job_repo.save(job)
    fetched_job = await job_repo.get_by_id(job_id)
    assert fetched_job is not None
    assert fetched_job.status == IngestionStatus.PROCESSING
    assert fetched_job.progress_pct == 55.0
