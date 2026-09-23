# ADR 0039: Standalone Ingestion Worker Daemon Architecture

## Status
Accepted

## Context
Document parsing, OCR, table extraction, chunking, and dense embedding generation are CPU and I/O intensive. Executing ingestion in-process within FastAPI request handlers starves HTTP worker threads, degrades API responsiveness, and risks thread starvation.

## Decision
We decouple asynchronous ingestion workloads into a dedicated background worker daemon (`src/financial_rag/worker.py`):
1. **Bounded Concurrency**: Uses an asynchronous semaphore (`asyncio.Semaphore(concurrency)`) to strictly cap parallel ingestion tasks per worker instance.
2. **Polling & Leases**: Workers query `PENDING` ingestion jobs from PostgreSQL with atomic state claiming (`PROCESSING`), updating progress milestones and heartbeats.
3. **Graceful Shutdown**: Intercepts `SIGINT` and `SIGTERM` signals, ceases new job acquisition, and allows active in-flight jobs to complete up to a configurable shutdown timeout (`WORKER_SHUTDOWN_TIMEOUT_SECONDS`).
4. **Context Propagation**: Preserves tenant context (`tenant_id`) and correlation tracing IDs (`job-{job_id}`) across all async spans.

## Consequences
### Positive
- API service remains purely stateless and responsive under heavy upload traffic.
- Workers scale independently based on queue backlog and CPU metrics.
- Fault isolation: A crashing worker process does not impact HTTP API availability.
