# SRE Runbook: Qdrant Vector Index Recovery & Deterministic Rebuild

## 1. Overview & Triggers
- **Severity**: Severity 1 (Critical) if outage; Severity 3 (Planned) if embedding model upgrade.
- **Triggers**:
  1. Qdrant storage volume corruption or node failure.
  2. Embedding model migration (e.g. transitioning from `text-embedding-3-small` to higher dimension model).
  3. Chunking strategy change requiring index regeneration.

---

## 2. Recovery Architecture

Vectors in Qdrant are **derived indexes**. The ground truth is persisted in:
- **PostgreSQL**: Stores all `Document`, `DocumentVersion`, and `DocumentChunk` records with text content, metadata, table structures, and tenant IDs.
- **S3 Storage**: Stores raw PDF files for historical provenance.

---

## 3. Step-by-Step Execution Procedure

1. **Verify Database Connectivity & Chunk Counts**:
   ```bash
   python scripts/restore_db.py
   ```

2. **Execute Deterministic Vector Rebuild Tool**:
   - For all tenants and documents:
   ```bash
   python scripts/rebuild_vectors.py --batch-size 50
   ```
   - For a specific single tenant:
   ```bash
   python scripts/rebuild_vectors.py --tenant-id "tenant_acme_corp" --batch-size 50
   ```
   - For a specific single document:
   ```bash
   python scripts/rebuild_vectors.py --document-id "doc_10k_2025"
   ```

3. **Verify Qdrant Point Count Matches PostgreSQL Chunks**:
   ```bash
   curl http://qdrant.financial-rag.internal:6333/collections/financial_chunks
   ```
   - Ensure `points_count` equals `SELECT count(*) FROM document_chunks`.

4. **Execute Post-Rebuild Smoke Test**:
   ```bash
   pytest tests/deployment/test_smoke.py
   ```
