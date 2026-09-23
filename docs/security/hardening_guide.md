# Production Security Hardening & Compliance Guide

## 1. Multi-Layer Defense in Depth

The Financial RAG Platform enforces security across 6 distinct architectural tiers:

```
[ Tier 1: Network & Edge ]       => Public Subnets, TLS 1.3, ALB WAF, Strict CIDRs
[ Tier 2: Container Runtime ]    => Non-Root User (UID 10001), Read-Only FS, Scanned Images
[ Tier 3: Compute Isolation ]    => Private Subnets, No Public IPs, Task IAM Roles
[ Tier 4: Storage Encryption ]   => Customer KMS Keys, S3 Block Public Access, SSE-KMS
[ Tier 5: Tenant Data Isolation] => Tenant Context Injection, Filtered Queries, Zero Leakage
[ Tier 6: App Secrets & Auth ]   => 32+ char JWT Keys, Scrypt Password Hash, Secrets Manager
```

---

## 2. Container Security & Image Hardening

1. **Multi-Stage Build**: Build compilers and header dependencies exist only in the temporary builder stage. The final runtime image contains zero build tools.
2. **Non-Root Execution**: Container explicitly executes as `USER 10001:10001` (`appuser`). Root permissions are prohibited.
3. **Automated Vulnerability Scanning**: CI workflows run Trivy vulnerability scanning on every container build before publishing to ECR.

---

## 3. Network Isolation & Security Groups

- **No Public Compute**: API and Worker tasks run strictly in `private_app` subnets with zero public IP assignment.
- **Micro-Segmentation**:
  - PostgreSQL RDS allows inbound port 5432 **only** from API and Worker security groups.
  - Redis ElastiCache allows inbound port 6379 **only** from API and Worker security groups.
  - Qdrant allows inbound port 6333 **only** from API and Worker security groups.
  - API tasks accept HTTP traffic on port 8000 **only** from the Application Load Balancer security group.

---

## 4. Encryption in Transit & At Rest

- **In Transit**:
  - External traffic: Enforced TLS 1.2+ / TLS 1.3 via ALB with AWS-managed ACM certificates.
  - Internal DB traffic: `rds.force_ssl = 1` enforced in PostgreSQL parameter group.
  - Internal Redis traffic: ElastiCache in-transit encryption (TLS) enabled.
  - S3 bucket: Enforced HTTPS requests only via bucket policy condition `aws:SecureTransport: "false" -> Deny`.
- **At Rest**:
  - S3 Document Storage: Encrypted via AWS KMS (`aws:kms`) using customer-managed key with annual automatic rotation.
  - RDS PostgreSQL: Encrypted EBS volumes via AWS KMS.
  - Redis: At-rest encryption enabled.

---

## 5. Startup Invariant Auditing

The application runs strict startup validation during FastAPI lifespan initialization (`validate_security_configuration`):
- Fails fast on startup if `jwt_secret_key` is < 32 characters or matches insecure defaults.
- Fails fast if debug/dev bypass flags are set in production.
