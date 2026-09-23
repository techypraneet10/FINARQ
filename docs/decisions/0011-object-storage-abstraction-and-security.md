# 11. Object Storage Abstraction and Security

Date: 2026-08-21

## Status

Accepted

## Context

Financial document artifacts (raw PDFs, parsed intermediate JSON representations, OCR caches) must be securely stored in durable object storage. Development and testing environments require local filesystem storage, while production environments deploy to cloud object storage (AWS S3, MinIO, Google Cloud Storage).

## Decision

1. **`ObjectStorageProtocol` Interface**:
   - Defines async operations: `upload`, `download`, `delete`, `exists`, `get_metadata`, `get_presigned_url`, and `health_check`.
2. **`FileSystemStorageAdapter`**:
   - Implements strict path traversal defense (`_resolve_path` verifies absolute destination resolves strictly within root directory).
   - Atomic writes via temporary `.tmp` files and filesystem renames to prevent partial file reads during concurrent uploads.
   - Sidecar metadata persistence in companion `.meta.json` files.
3. **`S3StorageAdapter`**:
   - Implements async AWS S3 / MinIO client via `aioboto3`.
   - Supports presigned download URLs with configurable expiration.
4. **Hierarchical Key Scheme**:
   - Standardized object key convention: `documents/{document_id}/versions/{version_id}/{sanitized_filename}`.

## Consequences

### Positive
- Zero external infrastructure required for local testing.
- Immune to directory traversal attacks via malicious filenames (e.g. `../../etc/passwd`).
- Atomic writes guarantee crash-resilient file persistence.

### Negative / Trade-offs
- Local filesystem storage is not distributed; multiple API replicas require shared NFS or S3 in production.
