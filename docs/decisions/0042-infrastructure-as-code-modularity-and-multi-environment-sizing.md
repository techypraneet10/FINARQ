# ADR 0042: Infrastructure as Code Modularity and Multi-Environment Sizing

## Status
Accepted

## Context
Infrastructure must be fully reproducible across development, staging, and production environments, while balancing high availability, compliance, and cloud hosting costs.

## Decision
We organize Terraform into reusable modules (`infra/modules/`) and environment root configurations (`infra/environments/`):
1. **Modules**:
   - `vpc`: Multi-AZ subnets (public, private-app, private-data) with route tables.
   - `rds_postgres`: PostgreSQL 16 RDS instance with KMS encryption, automated backups, and parameter groups.
   - `s3_storage`: Encrypted, versioned document storage with Intelligent-Tiering and Glacier archiving.
   - `qdrant`: Dedicated vector database ECS service on private DNS.
   - `redis`: High-availability ElastiCache Redis cluster.
   - `compute_api_worker`: ECS Fargate tasks and services for API and Ingestion Workers with IAM roles and CloudWatch logging.
   - `alb`: Public Application Load Balancer with TLS 1.3 listener and healthcheck target groups.
2. **Environment Sizing**:
   - **Dev**: Single-AZ RDS (`db.t4g.medium`), single NAT Gateway, low replica counts, cost-optimized.
   - **Staging**: Multi-AZ RDS (`db.r6g.large`), Multi-AZ Redis, 2 API / 2 Worker replicas, production-parity.
   - **Production**: Multi-AZ RDS (`db.r6g.xlarge`), Multi-AZ Redis (`cache.m6g.xlarge`), 4 API / 4 Worker replicas, Customer-Managed KMS Key, 30-day backups, strict deletion protection.

## Consequences
### Positive
- Modular DRY infrastructure code.
- Clear environment isolation and predictable cost controls.
