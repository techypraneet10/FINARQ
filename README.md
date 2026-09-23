# FINARQ — Financial Document Intelligence & Verified Reasoning Platform

> **Status: Production Engineering Health Verified**  
> *Note: Enterprise production financial intelligence and verified reasoning platform featuring a provider-agnostic LLM synthesis layer, 8-stage deterministic post-generation validation, bounded retry with safe deterministic fallback, Server-Sent Events (SSE) streaming, cryptographic answer caching, multi-style prompt templates with prompt injection defenses, and a modern React 18 / TypeScript intelligence workspace.*

---

## 1. Mission & Core Principles

**FINARQ** is an enterprise-grade financial document intelligence and verified reasoning platform designed for factual, verifiable, and numerically accurate analysis of complex financial documents (e.g., SEC 10-K/10-Q filings, earnings reports, bank statements, loan agreements).

### Core Architectural Principle
> **THE LLM IS NOT THE SOURCE OF TRUTH.**  
> Source documents are the sole ground truth. Numerical calculations must be executed deterministically. Every factual claim must provide auditable, page-level citation evidence. Zero cross-tenant data leakage is cryptographically and architecturally enforced. Primary UX Principle: **ANSWER + EVIDENCE + SOURCE + CALCULATION + CONFIDENCE/STATUS**.

---

## 2. Platform Architecture

```
financial-rag-platform/
├── frontend/                  # React 18 + TypeScript Financial Intelligence Workspace
│   ├── src/api/               # Typed API client, token rotation, RFC 7807 error parsing
│   ├── src/components/        # Feature views (Dashboard, Documents, Search, Ask, Evidence, Admin, Jobs)
│   ├── src/context/           # AuthContext (RBAC), WorkspaceContext (Citations), ThemeContext
│   ├── src/design-system/     # Glass cards, buttons, status badges, accounting tables, modals, drawers
│   ├── src/utils/             # Accounting formatters (1,234.50), XSS sanitization, telemetry
│   ├── Dockerfile             # Multi-stage container (Node build + Nginx Alpine)
│   └── nginx.conf             # Security headers, SPA fallback, API reverse proxy
├── src/financial_rag/
│   ├── domain/                # Core business models, entities, custom exceptions, pure protocols
│   ├── application/           # Use cases (Ingestion Service, Retrieval Service, Reasoning Service, Answer Orchestrator)
│   ├── infrastructure/        # Concrete adapters (PyMuPDF, BM25, Qdrant, CrossEncoder, Scrypt, JWT, PostgreSQL, S3, Resilience)
│   ├── api/                   # FastAPI routing, authentication & RBAC middleware, schemas, RFC 7807 problem details
│   ├── config/                # Pydantic Settings with env parsing, secret masking, timeouts & worker limits
│   ├── common/                # Shared primitives, types, and cross-cutting constants
│   └── worker.py              # Standalone background ingestion worker daemon
```

---

## 3. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind Tokens, Lucide Icons, Vitest
- **Backend API**: FastAPI & Uvicorn (ASGI), Python `>= 3.11`
- **Background Workers**: Asyncio Ingestion Worker Daemon with bounded semaphore concurrency
- **Hybrid Retrieval**: Okapi BM25 (financial tokenization) + Qdrant Dense Vector (`qdrant-client`)
- **Candidate Fusion & Reranking**: Reciprocal Rank Fusion (RRF, $k=60$) + Cross-Encoder Reranker
- **Deterministic Reasoning**: Decimal-precision calculator (11 operations, zero-division safety), structured fact extraction
- **Auditing & Grounding**: 8-stage post-generation answer validator, exact claim-to-chunk citation verification
- **Security & Tenancy**: Bearer JWT tokens, Scrypt password hashing, 4-tier RBAC, Row/Payload tenant isolation
- **Resilience**: 3-state Circuit Breaker, exponential backoff with full jitter and semantic error classification
- **Relational Persistence**: PostgreSQL 16 (Asyncpg), SQLAlchemy 2.0, Alembic migrations
- **Object Storage**: AWS S3 / MinIO (`aioboto3`), Local Filesystem
- **Infrastructure as Code**: Terraform (AWS VPC, RDS PostgreSQL, S3, Qdrant, ElastiCache Redis, ECS Fargate, ALB)
- **Containerization**: Hardened multi-stage Dockerfile (`USER 10001:10001`), Nginx Alpine SPA, Docker Compose
- **Testing**: 257 backend Pytest suites + 21 frontend Vitest suites (100% pass rate)

---

## 4. Quickstart & Local Orchestration (Docker Compose)

The fastest way to launch the full platform locally with PostgreSQL, Qdrant, MinIO, Redis, the API, Ingestion Worker, and Frontend Workspace:

```bash
# 1. Start complete stack with Docker Compose
docker compose up --build

# 2. Open the Financial Intelligence Workspace
# Navigate to: http://localhost:5173
```

### Running Frontend Locally in Development
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:5173 (proxies backend requests to http://127.0.0.1:8000)
```
git clone <repository_url>
cd financial-rag-platform

# 2. Configure local environment
cp .env.example .env

# 3. Start complete local stack
docker compose up --build
```

The services will become available at:
- **FastAPI Application**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Version Metadata**: `http://localhost:8000/version`
- **Prometheus Metrics**: `http://localhost:8000/metrics`
- **Qdrant Dashboard**: `http://localhost:6333/dashboard`
- **MinIO Console**: `http://localhost:9001` (Credentials: `minioadmin` / `minioadmin`)

---

## 5. Development & Operational Commands

| Action | Command |
| :--- | :--- |
| **Run API Server (Dev)** | `uvicorn financial_rag.main:app --reload --port 8000` |
| **Run Ingestion Worker** | `python -m financial_rag.worker` or `python scripts/run_worker.py` |
| **Run Database Migrations** | `python scripts/migrate.py` or `alembic upgrade head` |
| **Verify Restored Database**| `python scripts/restore_db.py` |
| **Rebuild Vector Store** | `python scripts/rebuild_vectors.py --batch-size 50` |
| **Run Load Benchmark** | `python scripts/load_test.py --concurrency 10 --requests 20` |
| **Run Smoke Tests** | `pytest tests/deployment/test_smoke.py -v` |
| **Run Complete Test Suite** | `pytest tests/ -v` |
| **Lint & Format Code** | `ruff check .` && `ruff format --check .` |
| **Static Type Check** | `mypy src scripts tests` |

---

## 6. Infrastructure as Code (Terraform)

Deploy to AWS environments via Terraform:

```bash
# Development
cd infra/environments/dev
terraform init && terraform apply

# Staging
cd infra/environments/staging
terraform init && terraform apply

# Production
cd infra/environments/production
terraform init && terraform apply
```

---

## 7. Architecture Documentation & Decision Records

Detailed architectural specifications, SRE runbooks, and decisions:
- [ARCHITECTURE.md](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/ARCHITECTURE.md)
- [SLO Framework](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/operations/slo_framework.md)
- [Production Alert Definitions](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/operations/alerts.md)
- [Disaster Recovery Plan](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/disaster-recovery/dr_plan.md)
- [Cloud Infrastructure Cost Model](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/architecture/cost_model.md)
- [Security Hardening Guide](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/security/hardening_guide.md)
- [SRE Incident Runbooks](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/operations/runbooks/)
- [Architecture Decision Records (0001 - 0047)](file:///c:/Users/Praneet/OneDrive/Desktop/financial-rag-platform/docs/decisions/)

