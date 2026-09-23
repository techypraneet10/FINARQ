# SRE Runbook: API 5xx Outage Incident Response

## 1. Overview & Severity
- **Severity**: Severity 1 (Critical)
- **Impact**: Inbound API requests are failing with 500/502/503/504 errors; users cannot query filings or synthesize answers.

---

## 2. Immediate Diagnostic Steps

1. **Check Live Service Health & Version**:
   ```bash
   curl -I https://api.financial-rag.yourdomain.com/health
   curl https://api.financial-rag.yourdomain.com/api/v1/version
   ```

2. **Inspect ECS Task Health in AWS Console / CLI**:
   ```bash
   aws ecs describe-services --cluster production-financial-rag-cluster --services production-financial-rag-api
   ```
   - Check if task count matches desired count.
   - Look for crashing containers with non-zero exit codes.

3. **Check CloudWatch Centralized Logs**:
   ```bash
   aws logs tail /ecs/production-financial-rag-api --follow --filter-pattern "CRITICAL"
   ```
   - Identify if failures stem from DB timeouts, LLM rate limits (429s), or unhandled exceptions.

4. **Verify Downstream Dependency Health**:
   - RDS PostgreSQL CPU & Connection counts.
   - Qdrant Vector Store HTTP reachability (`/readyz`).
   - Redis ElastiCache CPU & Memory.

---

## 3. Mitigation & Remediation Actions

- **Scenario A: Task Crash Loops (OOM / Faulty Deploy)**:
  - Immediately execute [Emergency Rollback](file:///docs/operations/runbooks/emergency_rollback.md) to previous known-good Git SHA.
- **Scenario B: Database Connection Exhaustion**:
  - Scale up connection pool limits or restart stuck tasks to drop idle pool connections.
- **Scenario C: LLM Vendor Outage**:
  - Verify circuit breaker state in `/metrics`. Ensure graceful fallback to cached responses or deterministic reasoning mode is operational.
