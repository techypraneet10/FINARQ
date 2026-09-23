# SRE Runbook: Emergency Production Rollback

## 1. Overview & Triggers
- **Severity**: Severity 1 (Critical)
- **Impact**: A new deployment introduced severe regressions, latency spikes, or 5xx outages requiring immediate reversal.

---

## 2. Emergency Automated ECS Rollback Procedure

1. **Locate Previous Known-Good ECR Image Tag / Task Definition**:
   ```bash
   aws ecs list-task-definitions --family-prefix production-financial-rag-api --sort DESC --max-items 5
   ```

2. **Rollback API ECS Service to Previous Revision**:
   ```bash
   aws ecs update-service \
     --cluster production-financial-rag-cluster \
     --service production-financial-rag-api \
     --task-definition production-financial-rag-api:<PREVIOUS_REVISION_NUMBER> \
     --force-new-deployment
   ```

3. **Rollback Worker ECS Service to Previous Revision**:
   ```bash
   aws ecs update-service \
     --cluster production-financial-rag-cluster \
     --service production-financial-rag-worker \
     --task-definition production-financial-rag-worker:<PREVIOUS_REVISION_NUMBER> \
     --force-new-deployment
   ```

4. **Wait for ECS Service Stability**:
   ```bash
   aws ecs wait services-stable \
     --cluster production-financial-rag-cluster \
     --services production-financial-rag-api production-financial-rag-worker
   ```

---

## 3. Database Schema Rollback (If Migrations Were Applied)

If the failed release applied destructive or breaking database migrations:

1. **Check Current Alembic Revision**:
   ```bash
   alembic current
   ```

2. **Downgrade to Target Revision**:
   ```bash
   alembic downgrade -1
   ```

3. **Verify Restored Schema Integrity**:
   ```bash
   python scripts/restore_db.py
   ```

4. **Run Smoke Tests to Confirm Restoration**:
   ```bash
   pytest tests/deployment/test_smoke.py
   ```
