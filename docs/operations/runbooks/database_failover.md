# SRE Runbook: PostgreSQL RDS Multi-AZ Failover & Recovery

## 1. Overview & Severity
- **Severity**: Severity 1 (Critical)
- **Impact**: Primary PostgreSQL database instance is degraded or unreachable; API/Worker sessions experiencing connection timeouts.

---

## 2. Automated Multi-AZ Failover

AWS RDS Multi-AZ automatically detects primary instance crashes and transitions DNS CNAME to the synchronous standby replica within **60 to 120 seconds**.

### Health Verification Commands
1. **Check RDS Instance Status via AWS CLI**:
   ```bash
   aws rds describe-db-instances --db-instance-identifier production-financial-rag-postgres \
     --query "DBInstances[0].[DBInstanceStatus,PendingModifiedValues,MultiAZ]"
   ```

2. **Verify Database Integrity via Automated Verification Tool**:
   ```bash
   python scripts/restore_db.py
   ```

---

## 3. Manual Failover Execution (If Primary is Unresponsive)

If automated failover does not trigger or primary node is exhibiting silent memory corruption:

1. **Trigger Immediate Forced Failover with Reboot**:
   ```bash
   aws rds reboot-db-instance \
     --db-instance-identifier production-financial-rag-postgres \
     --force-failover
   ```

2. **Monitor DNS Propagation & Connection Resumption**:
   - Connection pools in SQLAlchemy (`DatabaseSessionManager`) utilize `pool_pre_ping=True` and will automatically reconnect once DNS resolves to the promoted replica.

3. **Restart API & Worker Tasks (If Stale Pools Persist)**:
   ```bash
   aws ecs update-service --cluster production-financial-rag-cluster --service production-financial-rag-api --force-new-deployment
   aws ecs update-service --cluster production-financial-rag-cluster --service production-financial-rag-worker --force-new-deployment
   ```
