"""Integration tests verifying multi-tenant relational persistence boundaries."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from financial_rag.common.types import DocumentType
from financial_rag.config.settings import DatabaseSettings
from financial_rag.domain.entities.models import Document
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
from financial_rag.infrastructure.persistence.repositories import (
    PostgresDocumentRepository,
)


@pytest.fixture
async def db_mgr(tmp_path):
    db_file = tmp_path / "tenant_repo_test.db"
    mgr = DatabaseSessionManager(db_settings=DatabaseSettings(url=f"sqlite+aiosqlite:///{db_file}"))
    await mgr.create_all_tables()
    return mgr


@pytest.mark.asyncio
async def test_tenant_isolated_document_queries(db_mgr: DatabaseSessionManager) -> None:
    doc_repo = PostgresDocumentRepository(session_manager=db_mgr)

    tenant_a = "tenant-apple"
    tenant_b = "tenant-microsoft"

    # Create Document A under Tenant A
    doc_a = Document(
        id=str(uuid4()),
        tenant_id=tenant_a,
        title="Apple FY23 10-K",
        document_type=DocumentType.SEC_10K,
        ticker_symbol="AAPL",
        fiscal_year=2023,
        storage_uri=f"tenants/{tenant_a}/doc_a.pdf",
        file_hash_sha256="hash_a",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await doc_repo.save(doc_a)

    # Create Document B under Tenant B
    doc_b = Document(
        id=str(uuid4()),
        tenant_id=tenant_b,
        title="Microsoft FY23 10-K",
        document_type=DocumentType.SEC_10K,
        ticker_symbol="MSFT",
        fiscal_year=2023,
        storage_uri=f"tenants/{tenant_b}/doc_b.pdf",
        file_hash_sha256="hash_b",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    await doc_repo.save(doc_b)

    # 1. Direct fetch with matching tenant
    fetched_a = await doc_repo.get_by_id(doc_a.id, tenant_id=tenant_a)
    assert fetched_a is not None
    assert fetched_a.title == "Apple FY23 10-K"

    # 2. Direct IDOR attempt: fetch Doc A using Tenant B credentials MUST return None
    cross_fetched = await doc_repo.get_by_id(doc_a.id, tenant_id=tenant_b)
    assert cross_fetched is None

    # 3. List documents scoped by tenant
    list_a = await doc_repo.list_documents(tenant_id=tenant_a)
    assert len(list_a) == 1
    assert str(list_a[0].id) == str(doc_a.id)

    list_b = await doc_repo.list_documents(tenant_id=tenant_b)
    assert len(list_b) == 1
    assert str(list_b[0].id) == str(doc_b.id)

    # 4. Cross-tenant deletion attempt must fail
    deleted = await doc_repo.delete(doc_a.id, tenant_id=tenant_b)
    assert deleted is False

    # Verify Doc A is still present
    still_exists = await doc_repo.get_by_id(doc_a.id, tenant_id=tenant_a)
    assert still_exists is not None
