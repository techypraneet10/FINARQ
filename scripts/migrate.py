"""Controlled database migration execution runner using Alembic."""

import os
import sys

from alembic import command
from alembic.config import Config

from financial_rag.config.settings import get_settings
from financial_rag.infrastructure.logging import get_logger, setup_logging

logger = get_logger("financial_rag.scripts.migrate")


def run_migrations() -> None:
    """Execute Alembic migrations forward to head revision."""
    settings = get_settings()
    setup_logging(level=settings.logging.level, format_type=settings.logging.format)
    logger.info(
        f"Preparing to execute Alembic database migrations against environment [{settings.app.environment.value}]"
    )

    # Determine path to alembic.ini
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    alembic_ini_path = os.path.join(base_dir, "alembic.ini")

    if not os.path.exists(alembic_ini_path):
        logger.error(f"Alembic configuration file not found at: {alembic_ini_path}")
        sys.exit(1)

    alembic_cfg = Config(alembic_ini_path)

    # Set dynamic sqlalchemy.url from application database settings
    # Note: Alembic CLI uses synchronous driver or asyncpg through alembic/env.py
    connection_url = settings.database.connection_url
    alembic_cfg.set_main_option("sqlalchemy.url", connection_url)

    try:
        logger.info("Executing 'alembic upgrade head'...")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully.")
    except Exception as ex:
        logger.critical(f"Database migration failed: {ex}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    run_migrations()
