# Cloud Infrastructure Cost Model & Financial Sizing

## 1. Cost Overview Across Environments

Monthly cloud hosting costs are sized across development, staging, and production tiers on AWS (`us-east-1`):

| Component | Dev (Minimal) | Staging (Parity) | Production (High-Availability) |
| :--- | :--- | :--- | :--- |
| **ECS Fargate Compute (API)** | 1 task (0.5 vCPU / 1GB) ~$18/mo | 2 tasks (1 vCPU / 2GB) ~$72/mo | 4 tasks (2 vCPU / 4GB) ~$288/mo |
| **ECS Fargate Compute (Worker)**| 1 task (1 vCPU / 2GB) ~$36/mo | 2 tasks (2 vCPU / 4GB) ~$144/mo | 4 tasks (4 vCPU / 8GB) ~$576/mo |
| **RDS PostgreSQL 16** | `db.t4g.medium` (Single-AZ) ~$45/mo | `db.r6g.large` (Multi-AZ) ~$360/mo | `db.r6g.xlarge` (Multi-AZ) ~$720/mo |
| **ElastiCache Redis** | `cache.t4g.small` (Single node) ~$15/mo | `cache.m6g.large` (2 nodes) ~$190/mo | `cache.m6g.xlarge` (3 nodes) ~$570/mo |
| **Qdrant Vector Store** | 1 Fargate task (0.5 vCPU) ~$18/mo | 1 Fargate task (1 vCPU) ~$36/mo | 1 Fargate task (2 vCPU) ~$72/mo |
| **Application Load Balancer** | ~$25/mo | ~$25/mo | ~$35/mo |
| **NAT Gateway & Egress** | 1 NAT GW ~$35/mo | 2 NAT GWs ~$70/mo | 3 NAT GWs ~$105/mo |
| **S3 Storage (1TB + LifeCycle)**| ~$5/mo | ~$15/mo | ~$35/mo |
| **KMS, CloudWatch & Logs** | ~$10/mo | ~$25/mo | ~$65/mo |
| **Total Cloud Infra / Month** | **~$207 / month** | **~$937 / month** | **~$2,466 / month** |

---

## 2. LLM & Embedding Operational Unit Economics

| Operational Unit | Volume / Month | Model Used | Estimated Unit Cost | Monthly Total |
| :--- | :--- | :--- | :--- | :--- |
| **Dense Vector Embeddings** | 100,000 chunks (80M tokens) | `text-embedding-3-small` | $0.02 / 1M tokens | **$1.60 / mo** |
| **Verified Answer Synthesis** | 50,000 queries (150M tokens) | GPT-4o / Claude 3.5 Sonnet | $3.00 / 1M input, $15/1M out | **~$950.00 / mo** |
| **Cached Answer Inquiries** | 30,000 queries (Redis Hit) | Local Redis Cache | $0.00 / token | **$0.00** |
| **Total AI Inference / Month** | | | | **~$951.60 / month** |

---

## 3. Total Blended Cost per Query
- At 80,000 monthly queries:
  - Infrastructure: $2,466 / 80,000 = **$0.0308 / query**
  - LLM Inference: $951.60 / 80,000 = **$0.0118 / query**
  - **Total Cost per Financial Inquiry**: **~$0.0426 per verified answer**.
