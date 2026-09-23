# SRE Runbook: Background Ingestion Worker Backlog

## 1. Overview & Severity
- **Severity**: Severity 2 (High)
- **Impact**: Document ingestion jobs are accumulating in `PENDING` state; uploaded SEC filings are delayed in indexing.

---

## 2. Immediate Diagnostic Steps

1. **Check Job Queue Statistics in PostgreSQL**:
   ```sql
   SELECT status, current_stage, count(*) 
   FROM ingestion_jobs 
   GROUP BY status, current_stage;
   ```
   - Identify if jobs are stuck in `PENDING` (worker starvation) or `PROCESSING` (deadlocks / hangs).

2. **Inspect Worker Task Count & CPU Utilization**:
   ```bash
   aws ecs describe-services --cluster production-financial-rag-cluster --services production-financial-rag-worker
   ```

3. **Check Worker Logs for Timeouts or OCR Hangs**:
   ```bash
   aws logs tail /ecs/production-financial-rag-worker --follow --filter-pattern "ERROR"
   ```

---

## 3. Mitigation & Remediation Actions

1. **Scale Out Worker Tasks**:
   - Temporarily increase worker replica count from 4 to 8:
   ```bash
   aws ecs update-service --cluster production-financial-rag-cluster --service production-financial-rag-worker --desired-count 8
   ```

2. **Clear Poison Pill Jobs**:
   - If a specific corrupt PDF repeatedly crashes workers, locate its job ID and mark it `FAILED` manually with error details:
   ```sql
   UPDATE ingestion_jobs 
   SET status = 'failed', error_message = 'Corrupted PDF rejected during manual triage', completed_at = NOW() 
   WHERE id = '<corrupted-job-id>' AND status = 'processing';
   ```

3. **Scale Down After Queue Normalization**:
   - Once pending jobs count drops below 10, restore desired worker count to baseline (4).
