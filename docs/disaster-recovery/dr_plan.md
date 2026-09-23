# Disaster Recovery Plan & Business Continuity Architecture

## 1. Objectives & Compliance

- **Recovery Point Objective (RPO)**: **<= 15 minutes** (Maximum tolerable data loss period).
- **Recovery Time Objective (RTO)**: **<= 60 minutes** (Maximum tolerable service outage).
- **Target Compliance**: SOC 2 Type II, FINRA Books & Records (Rule 4511), SEC Rule 17a-4.

---

## 2. Tiered Persistence Recovery Architecture

```
[ Primary Region: us-east-1 ]                           [ Backup / DR Region: us-west-2 ]
+------------------------------------+                  +------------------------------------+
| S3 Documents Bucket (Encrypted)    | === (Cross-Reg) => | S3 Replica Bucket (Immutable Lock) |
| PostgreSQL RDS (Multi-AZ Primary)  | === (Snapshots) => | RDS Cross-Region Snapshot Copy     |
| Qdrant Vector Store (Fargate)      |                    | (Regenerated via rebuild_vectors)  |
| Redis ElastiCache Cluster          |                    | (Ephemeral Cache - Auto-Rebuild)   |
+------------------------------------+                  +------------------------------------+
```

---

## 3. Data Backup Strategies & Cadence

1. **PostgreSQL Relational Metadata**:
   - Continuous WAL archiving to S3 with point-in-time recovery (PITR) up to 30 days.
   - Automated daily snapshots copied across AWS regions.
2. **S3 Object Storage**:
   - S3 Bucket Versioning enabled with S3 Object Lock (WORM compliance).
   - Cross-Region Replication (CRR) to secondary region.
3. **Qdrant Vector Database**:
   - Derived index. Regenerated deterministically via `scripts/rebuild_vectors.py` in under 30 minutes for 1M vectors.

---

## 4. Disaster Recovery Scenarios & Execution

### Scenario A: Complete Primary AWS Availability Zone Outage
- **Mitigation**: Automated Multi-AZ failover handles compute (ECS tasks across 3 AZs) and database (RDS synchronous standby replica promotion) within 2 minutes with zero human intervention.

### Scenario B: Complete AWS Region Outage (us-east-1)
- **Mitigation**:
  1. Trigger Terraform apply in DR region:
     ```bash
     cd infra/environments/production
     terraform apply -var="aws_region=us-west-2"
     ```
  2. Restore RDS from latest cross-region snapshot.
  3. Run deterministic vector rebuild:
     ```bash
     python scripts/rebuild_vectors.py --batch-size 100
     ```
  4. Update Route53 DNS CNAME to secondary ALB.
  5. Verify health via `python scripts/restore_db.py` and `pytest tests/deployment/test_smoke.py`.
