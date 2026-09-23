"""SQLAlchemy 2.0 Async database engine and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from financial_rag.config.settings import DatabaseSettings, get_settings
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.persistence.database")


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM entities."""

    pass


class DatabaseSessionManager:
    """Manages asynchronous database engine and session life-cycle."""

    def __init__(self, db_settings: DatabaseSettings | None = None) -> None:
        self._settings = db_settings or get_settings().database
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self, custom_url: str | None = None) -> None:
        """Initialize async engine and session factory."""
        url = custom_url or self._settings.connection_url

        # Handle SQLite vs Postgres connection args
        is_sqlite = "sqlite" in url
        engine_kwargs: dict[str, object] = {
            "echo": self._settings.echo,
            "future": True,
        }

        if not is_sqlite:
            engine_kwargs.update(
                {
                    "pool_size": self._settings.pool_min_size,
                    "max_overflow": self._settings.pool_max_size - self._settings.pool_min_size,
                }
            )

        self._engine = create_async_engine(url, **engine_kwargs)

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
        logger.info(
            f"Database session manager initialized with dialect: {'sqlite' if is_sqlite else 'postgresql'}"
        )

    @property
    def engine(self) -> AsyncEngine:
        """Get initialized async engine."""
        if self._engine is None:
            self.initialize()
        assert self._engine is not None
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get session factory."""
        if self._session_factory is None:
            self.initialize()
        assert self._session_factory is not None
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide a transactional asynchronous database session."""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def create_all_tables(self) -> None:
        """Create all tables in database (used for testing environments)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all_tables(self) -> None:
        """Drop all tables in database (used for testing environments)."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def health_check(self) -> bool:
        """Verify database connectivity."""
        try:
            async with self.session() as sess:
                result = await sess.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as ex:
            logger.warning(f"Database health check failed: {ex}")
            return False

    async def close(self) -> None:
        """Close database engine connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database engine connections closed")


# Default global instance
db_manager = DatabaseSessionManager()
