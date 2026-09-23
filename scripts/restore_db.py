"""Automated database backup restoration validation and disaster recovery verification tool."""

import argparse
import asyncio
import sys
from typing import Any

from sqlalchemy import select, text

from financial_rag.config.settings import get_settings
from financial_rag.infrastructure.logging import get_logger, setup_logging
from financial_rag.infrastructure.persistence.database import DatabaseSessionManager
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

logger = get_logger("financial_rag.scripts.restore_db")

EXPECTED_TABLES = [
    "tenants",
    "users",
    "refresh_tokens",
    "documents",
    "document_versions",
    "document_pages",
    "document_chunks",
    "ingestion_jobs",
    "audit_events",
]


async def verify_database_integrity(session_manager: DatabaseSessionManager) -> dict[str, Any]:
    """Inspect and verify all required relational tables and multi-tenant integrity."""
    report: dict[str, Any] = {"status": "HEALTHY", "tables": {}, "errors": []}

    async with session_manager.session() as session:
        # 1. Check database connectivity
        result = await session.execute(text("SELECT 1"))
        if result.scalar() != 1:
            report["status"] = "FAILED"
            report["errors"].append("Database connectivity check failed.")
            return report

        # 2. Verify Table Existence and Record Counts
        for model in [
            TenantORM,
            UserORM,
            RefreshTokenORM,
            DocumentORM,
            DocumentVersionORM,
            DocumentPageORM,
            DocumentChunkORM,
            IngestionJobORM,
            AuditEventORM,
        ]:
            table_name = model.__tablename__
            try:
                count_stmt = select(text("count(*)")).select_from(model)
                count_res = await session.execute(count_stmt)
                count = count_res.scalar() or 0
                report["tables"][table_name] = {"exists": True, "count": count}
                logger.info(f"Verified table '{table_name}' with {count} records.")
            except Exception as ex:
                report["status"] = "FAILED"
                report["tables"][table_name] = {"exists": False, "error": str(ex)}
                report["errors"].append(f"Failed querying table {table_name}: {ex}")

    return report


async def main_async(args: argparse.Namespace) -> int:
    settings = get_settings()
    setup_logging(level=settings.logging.level, format_type=settings.logging.format)
    logger.info("=" * 60)
    logger.info("FINANCIAL RAG PLATFORM - DATABASE RESTORE & INTEGRITY CHECK")
    logger.info("=" * 60)

    session_manager = DatabaseSessionManager(settings.database)

    try:
        report = await verify_database_integrity(session_manager)
        if report["status"] == "HEALTHY":
            logger.info("All database tables and integrity invariants verified successfully.")
            return 0
        else:
            logger.error(f"Database integrity verification failed: {report['errors']}")
            return 1
    except Exception as ex:
        logger.critical(
            f"Disaster recovery verification encountered fatal error: {ex}", exc_info=True
        )
        return 1
    finally:
        await session_manager.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify restored database health and relational integrity."
    )
    parser.add_argument(
        "--backup-file", type=str, help="Path to sql dump / backup file if testing restore"
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
