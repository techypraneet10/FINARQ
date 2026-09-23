# ADR 0046: Database Migration Lifecycle and Schema Integrity Verification

## Status
Accepted

## Context
Database schema updates must execute reliably during continuous delivery without causing downtime, schema drift, or corrupted table states.

## Decision
We define a controlled migration lifecycle:
1. **Dedicated Migration Task (`scripts/migrate.py`)**: Migrations are decoupled from long-running API server lifespans. During deployment, a dedicated one-off container execution runs `python scripts/migrate.py` (`alembic upgrade head`) before updating application services.
2. **Backward-Compatible Schema Changes (Expand-Contract Pattern)**:
   - Expand: Add new columns/tables with nullable or default values.
   - Migrate: Deploy application code writing to new structures.
   - Contract: Remove obsolete columns/tables in subsequent releases.
3. **Automated Schema Integrity Checks (`scripts/restore_db.py`)**: Post-migration and restore scripts verify that all 9 core tables (`tenants`, `users`, `refresh_tokens`, `documents`, `document_versions`, `document_pages`, `document_chunks`, `ingestion_jobs`, `audit_events`) exist with intact foreign key relationships.

## Consequences
### Positive
- Prevents database deadlocks and lock contention during container startup.
- Enables zero-downtime rolling schema migrations.
