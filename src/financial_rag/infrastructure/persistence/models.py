"""SQLAlchemy 2.0 ORM models for relational persistence and multi-tenancy."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from financial_rag.infrastructure.persistence.database import Base


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


class TenantORM(Base):
    """Relational table mapping for Tenant organization boundary."""

    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    users: Mapped[list["UserORM"]] = relationship(
        "UserORM",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )


class UserORM(Base):
    """Relational table mapping for User identity."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="member")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    tenant: Mapped["TenantORM"] = relationship("TenantORM", back_populates="users")
    refresh_tokens: Mapped[list["RefreshTokenORM"]] = relationship(
        "RefreshTokenORM",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class RefreshTokenORM(Base):
    """Relational table mapping for refresh token rotation and revocation tracking."""

    __tablename__ = "refresh_tokens"

    token_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    rotated_to_token_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Relationships
    user: Mapped["UserORM"] = relationship("UserORM", back_populates="refresh_tokens")


class AuditEventORM(Base):
    """Relational table mapping for immutable security audit events."""

    __tablename__ = "audit_events"

    event_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    tenant_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    outcome: Mapped[str] = mapped_column(String(50), nullable=False)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    __table_args__ = (Index("ix_audit_tenant_time", "tenant_id", "timestamp"),)


class DocumentORM(Base):
    """Relational table mapping for core financial Document entity."""

    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, default="default_tenant", index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    ticker_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    fiscal_year: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    fiscal_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pages_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_version_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    # Relationships
    versions: Mapped[list["DocumentVersionORM"]] = relationship(
        "DocumentVersionORM",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersionORM.version_number",
    )
    pages: Mapped[list["DocumentPageORM"]] = relationship(
        "DocumentPageORM",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["DocumentChunkORM"]] = relationship(
        "DocumentChunkORM",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    jobs: Mapped[list["IngestionJobORM"]] = relationship(
        "IngestionJobORM",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    __table_args__ = (Index("ix_doc_tenant_ticker", "tenant_id", "ticker_symbol"),)


class DocumentVersionORM(Base):
    """Relational table mapping for immutable DocumentVersion snapshots."""

    __tablename__ = "document_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, default="default_tenant", index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    file_hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False, default="application/pdf")
    pages_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    document: Mapped["DocumentORM"] = relationship("DocumentORM", back_populates="versions")
    pages: Mapped[list["DocumentPageORM"]] = relationship(
        "DocumentPageORM",
        back_populates="version",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["DocumentChunkORM"]] = relationship(
        "DocumentChunkORM",
        back_populates="version",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("document_id", "version_number", name="uq_document_version_number"),
    )


class DocumentPageORM(Base):
    """Relational table mapping for extracted DocumentPage representations."""

    __tablename__ = "document_pages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, default="default_tenant", index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(50), nullable=False, default="native")
    has_images: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    width: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    height: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    blocks_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    tables_json: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Relationships
    document: Mapped["DocumentORM"] = relationship("DocumentORM", back_populates="pages")
    version: Mapped["DocumentVersionORM"] = relationship(
        "DocumentVersionORM", back_populates="pages"
    )

    __table_args__ = (
        UniqueConstraint("version_id", "page_number", name="uq_version_page_number"),
        Index("ix_pages_doc_page", "document_id", "page_number"),
    )


class DocumentChunkORM(Base):
    """Relational table mapping for generated DocumentChunk items."""

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, default="default_tenant", index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    page_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    page_numbers_json: Mapped[list[int]] = mapped_column(JSON, nullable=False, default=list)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_type: Mapped[str] = mapped_column(String(50), nullable=False, default="text")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_block_ids_json: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    section_path: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    table_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    char_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationships
    document: Mapped["DocumentORM"] = relationship("DocumentORM", back_populates="chunks")
    version: Mapped["DocumentVersionORM"] = relationship(
        "DocumentVersionORM", back_populates="chunks"
    )

    __table_args__ = (
        Index("ix_chunks_doc_index", "document_id", "chunk_index"),
        Index("ix_chunks_version", "version_id"),
        Index("ix_chunks_tenant", "tenant_id"),
    )


class IngestionJobORM(Base):
    """Relational table mapping for tracking asynchronous IngestionJob lifecycle."""

    __tablename__ = "ingestion_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), nullable=False, default="default_tenant", index=True
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_id: Mapped[str] = mapped_column(String(36), nullable=False, default="")
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True, default="pending")
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False, default="queued")
    progress_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    chunks_indexed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_stage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    error_details_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, index=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    document: Mapped["DocumentORM"] = relationship("DocumentORM", back_populates="jobs")

    __table_args__ = (Index("ix_jobs_tenant_status", "tenant_id", "status"),)
