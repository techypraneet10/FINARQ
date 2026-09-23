"""Persistence infrastructure package with multi-tenant relational models and repositories."""

from financial_rag.infrastructure.persistence.database import (
    Base,
    DatabaseSessionManager,
    db_manager,
)
from financial_rag.infrastructure.persistence.models import (
    AuditEventORM,
    DocumentChunkORM,
    DocumentORM,
    DocumentPageORM,
    DocumentVersionORM,
    IngestionJobORM,
    RefreshTokenORM,
    TenantORM,
    UserORM,
)
from financial_rag.infrastructure.persistence.repositories import (
    PostgresAuditEventRepository,
    PostgresDocumentChunkRepository,
    PostgresDocumentPageRepository,
    PostgresDocumentRepository,
    PostgresDocumentVersionRepository,
    PostgresIngestionJobRepository,
    PostgresRefreshTokenRepository,
    PostgresTenantRepository,
    PostgresUserRepository,
)

__all__ = [
    "AuditEventORM",
    "Base",
    "DatabaseSessionManager",
    "DocumentChunkORM",
    "DocumentORM",
    "DocumentPageORM",
    "DocumentVersionORM",
    "IngestionJobORM",
    "PostgresAuditEventRepository",
    "PostgresDocumentChunkRepository",
    "PostgresDocumentPageRepository",
    "PostgresDocumentRepository",
    "PostgresDocumentVersionRepository",
    "PostgresIngestionJobRepository",
    "PostgresRefreshTokenRepository",
    "PostgresTenantRepository",
    "PostgresUserRepository",
    "RefreshTokenORM",
    "TenantORM",
    "UserORM",
    "db_manager",
]
