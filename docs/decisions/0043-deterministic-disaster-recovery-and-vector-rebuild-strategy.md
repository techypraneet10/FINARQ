# ADR 0043: Deterministic Disaster Recovery and Vector Rebuild Strategy

## Status
Accepted

## Context
In the event of catastrophic failure, data corruption, or embedding model upgrades, the platform must recover primary relational data and rebuild vector search indexes without data loss.

## Decision
We define a decoupled disaster recovery and vector rebuild strategy:
1. **Primary Ground Truth**: PostgreSQL is the authoritative relational store for documents, versions, chunks, tables, and tenant metadata. S3 is the authoritative store for raw PDF artifacts.
2. **Deterministic Vector Rebuild Tool (`scripts/rebuild_vectors.py`)**:
   - Queries verified chunks from PostgreSQL.
   - Batch-embeds text using the active embedding model and dimension.
   - Upserts vectors into Qdrant with complete tenant payload contracts.
3. **Database Restore Verification (`scripts/restore_db.py`)**:
   - Automates post-restore health verification, checking table existence, record integrity, and application connectivity.
4. **Recovery Objectives**: RPO <= 15 minutes (via automated RDS snapshots and S3 versioning), RTO <= 1 hour (via automated Terraform provisioning and rebuild scripts).

## Consequences
### Positive
- Vector databases are treated as regenerable derived indexes, eliminating split-brain risks.
- Predictable and testable disaster recovery runbooks.
