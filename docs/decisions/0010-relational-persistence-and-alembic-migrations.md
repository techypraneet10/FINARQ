# 10. Relational Persistence and Alembic Migrations

Date: 2026-08-21

## Status

Accepted

## Context

Document metadata, version histories, parsed layout structures, financial tables, chunks, and background ingestion jobs require transactional ACID guarantees, relational integrity, and schema migration capabilities.

## Decision

1. **SQLAlchemy 2.0 Async ORM**:
   - Implements async ORM models using `DeclarativeBase` and `Mapped[...]` type annotations.
   - Models: `DocumentModel`, `DocumentVersionModel`, `DocumentPageModel`, `DocumentChunkModel`, `IngestionJobModel`.
2. **PostgreSQL as Primary & Async SQLite for Local/Unit Testing**:
   - `DatabaseSessionManager` supports both PostgreSQL (`postgresql+asyncpg://`) and local async SQLite (`sqlite+aiosqlite://`).
   - Generic JSONB/JSON column mappings adapt cleanly across both database dialects.
3. **Repository Pattern**:
   - Domain logic interacts strictly via repository protocols (`DocumentRepositoryProtocol`, `DocumentVersionRepositoryProtocol`, `DocumentPageRepositoryProtocol`, `DocumentChunkRepositoryProtocol`, `IngestionJobRepositoryProtocol`).
   - Concrete implementations (`PostgresDocumentRepository`, etc.) encapsulate all SQL queries, pagination, and domain entity mapping.
4. **Alembic Async Migrations**:
   - Async migration environment configured in `alembic/env.py`.
   - Initial schema migration created in `alembic/versions/0001_phase1_initial_schema.py`.

## Consequences

### Positive
- Strict referential integrity (foreign keys, cascading deletes, unique constraints on `(document_id, version_number)`).
- Schema evolution tracked through version-controlled migrations.
- Unit and integration tests run entirely locally with zero external network dependencies via in-memory or temporary SQLite databases.

### Negative / Trade-offs
- Dialect discrepancies between PostgreSQL and SQLite JSON capabilities require defensive JSON serialization helpers.
