"""Phase 10 & 14 Multi-Tenancy, Identity, and Security Relational Schema.

Revision ID: 0002_phase10_security_schema
Revises: 0001_phase1_initial_schema
Create Date: 2026-08-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_phase10_security_schema"
down_revision: str | None = "0001_phase1_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Tenants Table
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_status", "tenants", ["status"])

    # 2. Users Table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_status", "users", ["status"])

    # 3. Refresh Tokens Table
    op.create_table(
        "refresh_tokens",
        sa.Column("token_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rotated_to_token_id", sa.String(length=36), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_tenant_id", "refresh_tokens", ["tenant_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_revoked", "refresh_tokens", ["revoked"])

    # 4. Audit Events Table
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=True),
        sa.Column("actor_user_id", sa.String(length=36), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("outcome", sa.String(length=50), nullable=False),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("source_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"])
    op.create_index("ix_audit_events_tenant_id", "audit_events", ["tenant_id"])
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"])
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_tenant_time", "audit_events", ["tenant_id", "timestamp"])

    # 5. Add tenant_id and user_id to existing tables
    op.add_column(
        "documents",
        sa.Column(
            "tenant_id", sa.String(length=36), nullable=False, server_default="default_tenant"
        ),
    )
    op.add_column(
        "documents",
        sa.Column("user_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])
    op.create_index("ix_doc_tenant_ticker", "documents", ["tenant_id", "ticker_symbol"])

    op.add_column(
        "document_versions",
        sa.Column(
            "tenant_id", sa.String(length=36), nullable=False, server_default="default_tenant"
        ),
    )
    op.create_index("ix_document_versions_tenant_id", "document_versions", ["tenant_id"])

    op.add_column(
        "document_pages",
        sa.Column(
            "tenant_id", sa.String(length=36), nullable=False, server_default="default_tenant"
        ),
    )
    op.create_index("ix_document_pages_tenant_id", "document_pages", ["tenant_id"])

    op.add_column(
        "document_chunks",
        sa.Column(
            "tenant_id", sa.String(length=36), nullable=False, server_default="default_tenant"
        ),
    )
    op.create_index("ix_document_chunks_tenant_id", "document_chunks", ["tenant_id"])

    op.add_column(
        "ingestion_jobs",
        sa.Column(
            "tenant_id", sa.String(length=36), nullable=False, server_default="default_tenant"
        ),
    )
    op.add_column(
        "ingestion_jobs",
        sa.Column("user_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_ingestion_jobs_tenant_id", "ingestion_jobs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_jobs_tenant_id", table_name="ingestion_jobs")
    op.drop_column("ingestion_jobs", "user_id")
    op.drop_column("ingestion_jobs", "tenant_id")

    op.drop_index("ix_document_chunks_tenant_id", table_name="document_chunks")
    op.drop_column("document_chunks", "tenant_id")

    op.drop_index("ix_document_pages_tenant_id", table_name="document_pages")
    op.drop_column("document_pages", "tenant_id")

    op.drop_index("ix_document_versions_tenant_id", table_name="document_versions")
    op.drop_column("document_versions", "tenant_id")

    op.drop_index("ix_doc_tenant_ticker", table_name="documents")
    op.drop_index("ix_documents_tenant_id", table_name="documents")
    op.drop_column("documents", "user_id")
    op.drop_column("documents", "tenant_id")

    op.drop_table("audit_events")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("tenants")
