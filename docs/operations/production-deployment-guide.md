# Financial RAG Platform — Production Deployment Guide

## 1. Overview
This guide provides complete end-to-end instructions for deploying the Financial RAG Platform to production on AWS using Terraform and Docker.

---

## 2. Architecture Overview
The platform deploys as an enterprise-grade, highly available microservices topology:
- **Compute**: AWS ECS Fargate running FastAPI API services (2–10 autoscale tasks) and asynchronous Ingestion Worker daemons (2–8 autoscale tasks).
- **Edge / Load Balancer**: AWS Application Load Balancer (ALB) with AWS WAF and ACM TLS 1.3 certificate.
- **Relational Metadata**: AWS RDS PostgreSQL 16 Multi-AZ (`db.r6g.xlarge`) with KMS master key encryption.
- **Vector Database**: High-availability Qdrant cluster with persistent storage and service discovery.
- **Cache & Locks**: AWS ElastiCache Redis 7 Replication Group with in-transit and at-rest encryption.
- **Object Storage**: Amazon S3 document buckets with customer KMS encryption and S3 Block Public Access.

---

## 3. Deployment Prerequisites

1. **AWS CLI & IAM Permissions**:
   - Configured with Administrator or dedicated CI/CD deployment role.
2. **Terraform CLI**:
   - Version `>= 1.5.0`.
3. **Docker Engine**:
   - Version `>= 24.0.0` with Buildx.
4. **Environment Secrets**:
   - Store production database credentials, JWT secret keys, and LLM API keys in AWS Secrets Manager or Parameter Store.

---

## 4. Step-by-Step Production Deployment

### Step 1: Provision Infrastructure with Terraform
```bash
cd infra/environments/production
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### Step 2: Build & Push Container Images to Amazon ECR
```bash
# Authenticate Docker to Amazon ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com

# Build multi-stage hardened image
docker build -t <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/financial-rag:v1.0.0-prod -f docker/Dockerfile .

# Push image
docker push <AWS_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/financial-rag:v1.0.0-prod
```

### Step 3: Execute Database Migrations
Run the one-off Alembic migration task on ECS Fargate:
```bash
aws ecs run-task \
  --cluster production-financial-rag-cluster \
  --task-definition production-financial-rag-migration \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<PRIVATE_SUBNETS>],securityGroups=[<MIGRATION_SG>]}"
```

### Step 4: Deploy ECS Services (Zero-Downtime Rolling Update)
```bash
aws ecs update-service \
  --cluster production-financial-rag-cluster \
  --service production-financial-rag-api \
  --force-new-deployment

aws ecs update-service \
  --cluster production-financial-rag-cluster \
  --service production-financial-rag-worker \
  --force-new-deployment

# Wait for deployment stability
aws ecs wait services-stable \
  --cluster production-financial-rag-cluster \
  --services production-financial-rag-api production-financial-rag-worker
```

### Step 5: Post-Deployment Smoke Verification
```bash
export DEPLOY_TARGET_URL="https://api.financial-rag.example.com"
pytest tests/deployment/test_smoke.py -v
```
