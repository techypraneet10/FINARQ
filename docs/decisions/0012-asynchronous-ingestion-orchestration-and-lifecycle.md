# 12. Asynchronous Ingestion Orchestration and Lifecycle

Date: 2026-08-21

## Status

Accepted

## Context

Financial document parsing, OCR, table extraction, normalization, chunking, and embedding generation for large multi-hundred-page annual reports (10-K) take several seconds to minutes. Performing ingestion synchronously within an HTTP request causes gateway timeouts (HTTP 504), blocks connection pools, and risks silent partial failures.

## Decision

1. **Two-Phase Ingestion Lifecycle**:
   - **Phase A (Synchronous HTTP Registration)**:
     - `POST /api/v1/documents` accepts multipart file upload.
     - Performs fast SHA-256 binary hashing, validation (magic bytes, size limits, filename sanitization), and duplicate detection.
     - Persists `Document`, `DocumentVersion`, and `IngestionJob` (status `PENDING`).
     - Stores raw binary to object storage.
     - Returns HTTP 201 Created immediately with `document_id`, `version_id`, `job_id`, and status `PENDING`.
   - **Phase B (Asynchronous Execution & Progress Tracking)**:
     - Triggers pipeline execution in the background.
     - Updates `IngestionJob.stage` and `progress_pct` across sequential stages: `VALIDATING` -> `PARSING` -> `EXTRACTING_TABLES` -> `NORMALIZING` -> `STRUCTURE_DETECTION` -> `CHUNKING` -> `EMBEDDING` -> `INDEXING` -> `COMPLETED`.
     - In case of failure, records `error_message`, marks job `FAILED`, and increments `retry_count`.
2. **Job Inspection & Retry API**:
   - `GET /api/v1/ingestion-jobs/{job_id}`: Polls real-time stage, progress percentage, pages processed, and chunks indexed.
   - `POST /api/v1/ingestion-jobs/{job_id}/retry`: Retries a failed or stalled ingestion job.

## Consequences

### Positive
- Client responsiveness is instantaneous regardless of document size.
- Granular stage and percentage observability for UI dashboards and operations monitoring.
- Safe retry capability without re-uploading large binaries.

### Negative / Trade-offs
- Clients must poll job endpoints or receive webhook events to determine final indexing completion.
