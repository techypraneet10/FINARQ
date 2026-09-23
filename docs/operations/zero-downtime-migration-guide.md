# Financial RAG Platform — Zero-Downtime Schema Migration Guide

## 1. Principles of Zero-Downtime Migrations
To ensure zero service disruption during production schema evolution, all database modifications must follow the **Expand-Contract (Parallel Run) Pattern**.

Old application versions and new application versions must be able to operate concurrently against the database during rolling updates.

---

## 2. Expand-Contract Workflow

```
[ Phase 1: Expand ]
  - Add new columns (nullable or with server defaults).
  - Add new tables.
  - Create non-blocking indices (`CREATE INDEX CONCURRENTLY`).
  - Deploy migration BEFORE application update.
  - Old app version ignores new fields.

[ Phase 2: Dual Write & Rolling Deploy ]
  - Deploy new application version.
  - New app version reads/writes new columns with fallbacks.

[ Phase 3: Contract ]
  - In a subsequent release, backfill legacy data.
  - Apply NOT NULL constraints if needed.
  - Remove deprecated legacy columns/tables.
```

---

## 3. Migration Rules & Invariants

1. **Never rename columns directly**: Add a new column, dual-write in code, backfill data, and drop the old column in a later release.
2. **Never add NOT NULL columns without default values**: Always provide a `server_default` or make the column nullable initially.
3. **Always lock tables safely**: Avoid operations that acquire exclusive table locks (`ACCESS EXCLUSIVE`) for long durations.
4. **Idempotent migration scripts**: All Alembic migrations must be testable via `alembic upgrade head` followed by `alembic downgrade -1` in CI.

---

## 4. Execution Procedures

### Pre-Deployment Verification:
```bash
# Test migration on local staging database
python scripts/migrate.py
```

### Production Migration Execution:
Execute migration as a one-off Fargate task before triggering rolling service updates:
```bash
python scripts/migrate.py
```
