# Financial RAG Platform — Production Release Checklist

## 1. Pre-Release Phase (T-24h)
- [ ] **CI Pipeline Green**: All unit, integration, load, security, and benchmark tests pass on `main`.
- [ ] **Static Analysis Clean**: Zero Ruff linting issues and zero MyPy type errors.
- [ ] **Security Vulnerability Scan**: Trivy container vulnerability scan shows 0 Critical and 0 High vulnerabilities.
- [ ] **Database Migration Review**: Schema migrations reviewed for zero-downtime expand-contract compliance.
- [ ] **Staging Verification**: Staging deployment completed and all smoke tests passed.
- [ ] **Release Tag Created**: Semantic release tag created (e.g. `v1.0.0`).

---

## 2. Deployment Phase (T-0)
- [ ] **Backup Snapshot**: Trigger manual RDS PostgreSQL snapshot before deployment.
- [ ] **Database Migration Execution**: Trigger ECS Fargate migration task and verify `alembic upgrade head` success.
- [ ] **API Rolling Deployment**: Trigger ECS Fargate API service rolling update.
- [ ] **Worker Rolling Deployment**: Trigger ECS Fargate Worker daemon rolling update.
- [ ] **ECS Task Health**: Confirm minimum healthy percentage (100%) maintained throughout rolling update.

---

## 3. Post-Deployment Verification (T+15m)
- [ ] **Liveness Probe**: `GET /health` returns HTTP 200 `healthy`.
- [ ] **Readiness Probe**: `GET /ready` returns HTTP 200 with all downstream dependencies healthy.
- [ ] **Version Endpoint**: `GET /version` returns new semantic version and git commit SHA.
- [ ] **Smoke Test Suite**: Run `pytest tests/deployment/test_smoke.py -v`.
- [ ] **Prometheus Metrics**: Scrape `/metrics` to ensure traffic flows and error rates remain at 0%.
- [ ] **Error Logs**: CloudWatch logs show zero critical startup or runtime exceptions.

---

## 4. Rollback Plan
If post-deployment smoke tests fail or error rate exceeds SLO threshold (> 0.1%):
1. **Roll back ECS services**: Update ECS task definition revision to previous stable version.
2. **Database Rollback (if applicable)**: Run `alembic downgrade` only if strictly backward-compatible.
3. **Notify Engineering Team & Stakeholders**: Open incident investigation ticket.
