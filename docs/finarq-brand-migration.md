# FINARQ — Brand / Name Migration Report
**VERIDEX → FINARQ**
*Financial Document Intelligence & Verified Reasoning Platform*

---

## 1. Executive Summary

This document records the complete, verified branding and naming migration from **VERIDEX** to **FINARQ**. The migration strictly adheres to the Safe Replacement Policy: all user-facing branding, application metadata, documentation, and configuration templates were updated while 100% preserving core domain logic, numerical reasoning engines, vector pipelines, relational schemas, and API contracts.

- **Old Project Name:** `VERIDEX` (lowercase: `veridex`)
- **New Project Name:** `FINARQ` (lowercase: `finarq`)
- **Canonical Product Description:** `FINARQ — Financial Document Intelligence & Verified Reasoning Platform`

---

## 2. Inventory of Files Changed (18 Files)

| Area | File Path | Description of Changes |
|---|---|---|
| **Frontend Brand** | `frontend/src/components/brand/Logo.tsx` | Updated brand text from `VERIDEX` to `FINARQ`; preserved geometric verification prism mark and operational pulse. |
| **Frontend HTML** | `frontend/index.html` | Updated HTML title to `FINARQ \| Financial Document Intelligence & Verified Reasoning Platform` and meta description. |
| **Frontend Nav** | `frontend/src/components/layout/Sidebar.tsx` | Updated workspace navigation tab label to `Ask FINARQ`. |
| **Frontend View** | `frontend/src/components/dashboard/DashboardView.tsx` | Updated workspace badge to `FINARQ Workspace` and quick action button to `Ask FINARQ`. |
| **Frontend Auth** | `frontend/src/components/auth/LoginForm.tsx` | Updated subtitle to canonical `Financial Document Intelligence & Verified Reasoning Platform`. |
| **Frontend Tests**| `frontend/src/__tests__/auth_and_routing.test.tsx` | Updated brand text assertion to expect `FINARQ`. |
| **Backend Config**| `src/financial_rag/config/settings.py` | Updated default `AppSettings.name` to `"FINARQ"`. |
| **Backend Core**  | `src/financial_rag/main.py` | Updated FastAPI application description to canonical product description. |
| **Environment**   | `.env` | Updated `APP_NAME="FINARQ"`. |
| **Template Env**  | `.env.example` | Updated header and `APP_NAME="FINARQ"`. |
| **Orchestration** | `docker-compose.yml` | Updated `APP_NAME=FINARQ` in API service definition. |
| **Backend Tests** | `tests/unit/test_config.py` | Updated default `settings.app.name` assertion to `"FINARQ"`. |
| **Backend Tests** | `tests/integration/test_phase15_deployment_readiness.py` | Updated test fixture app name to `"FINARQ"`. |
| **Backend Tests** | `tests/integration/test_phase16_e2e_release_gate.py` | Updated test fixture app name to `"FINARQ"`. |
| **Documentation** | `README.md` | Updated product title, header, and mission statement to FINARQ. |
| **Documentation** | `ARCHITECTURE.md` | Updated system architecture title and mission to FINARQ. |
| **Documentation** | `docs/final-engineering-audit.md` | Updated active audit references to FINARQ. |
| **Documentation** | `docs/veridex-ui-redesign.md` | Updated product name to FINARQ while maintaining historical context notes. |

---

## 3. Files Intentionally Not Changed (Preserved Architecture)

The following core components were intentionally left untouched to prevent breaking dependencies, API contracts, or historical records:
- **Python Package Name:** `src/financial_rag/` (Preserved to maintain package imports and avoid regression).
- **Domain Models & Interfaces:** `src/financial_rag/domain/*` (All AST calculations, entities, protocols preserved).
- **Retrieval & Ingestion Engine:** `src/financial_rag/infrastructure/retrieval/*`, `src/financial_rag/infrastructure/parsing/*`.
- **Database Migrations & Schemas:** `src/financial_rag/infrastructure/persistence/*`, `alembic.ini`.
- **Architecture Decision Records:** `docs/decisions/` (Preserved immutable historical decision records).

---

## 4. User-Facing Branding Changes

1. **Logo & Verification Prism:**
   - Text updated from `VERIDEX` to `FINARQ`.
   - Multi-facet geometric verification prism mark and live emerald pulse indicator preserved.
2. **Page Title & Metadata:**
   - `<title>` rendered as `FINARQ | Financial Document Intelligence & Verified Reasoning Platform`.
   - `<meta name="description">` reflects FINARQ grounded intelligence.
3. **Workspace Shell & Navigation:**
   - Top sidebar brand header renders `FINARQ`.
   - Workspace navigation displays `Ask FINARQ`.
   - Dashboard welcome header displays `FINARQ Workspace` badge and `Ask FINARQ` quick trigger.
4. **Login Screen:**
   - Prominently displays `FINARQ` brand logo and canonical description: `Financial Document Intelligence & Verified Reasoning Platform`.

---

## 5. Backend Metadata Changes

1. **FastAPI Application:**
   - `app.title`: Configured from `AppSettings.name` (`"FINARQ"`).
   - `app.description`: `"Financial Document Intelligence & Verified Reasoning Platform. Grounded, fact-checked RAG with deterministic numerical reasoning."`.
2. **Endpoints:**
   - `GET /health` &rarr; `{"status": "healthy", "app_name": "FINARQ", "version": "0.1.0", ...}`
   - `GET /version` &rarr; `{"application": "FINARQ", "version": "0.1.0", "git_sha": "dev-local", ...}`
   - `GET /ready` &rarr; `{"status": "ready", ...}`
   - `GET /openapi.json` &rarr; Title: `"FINARQ"`.

---

## 6. Configuration & Docker Changes

- **`.env.example` & `.env`:** Configured `APP_NAME="FINARQ"`.
- **`docker-compose.yml`:** Set `APP_NAME=FINARQ` for the API container.
- **Preserved Configurations:** Database URLs, PostgreSQL credentials, Redis ports, Qdrant collection settings, S3 storage buckets, and security signing keys were strictly preserved without modification.

---

## 7. Compatibility Considerations

- **API Routes:** All existing routes (`/api/v1/documents`, `/api/v1/answers`, `/health`, `/ready`, `/version`, `/metrics`) maintain full backwards compatibility.
- **Database Schemas:** No database schema alterations or migrations were introduced.
- **Client Tokens:** JWT token schemas and tenant isolation mechanics remain unchanged.

---

## 8. Remaining VERIDEX References Audit

A repository-wide audit found exactly **2** remaining references, all classified as legitimate historical records:
1. `docs/veridex-ui-redesign.md:8`: `**Product Name:** FINARQ (formerly VERIDEX)` (Historical record note).
2. `docs/veridex-ui-redesign.md:228`: `- docs/veridex-ui-redesign.md` (Self-referential file inventory path).

Zero accidental user-facing VERIDEX references exist.

---

## 9. Verification & Quality Assurance Results

| Test Category | Command | Result | Details |
|---|---|---|---|
| **Backend Test Suite** | `pytest tests/` | **PASS** | 353 passed in 28.50s (100% pass rate) |
| **Frontend Test Suite** | `npm test -- --run` | **PASS** | 4 test files passed, 21 tests passed cleanly |
| **Frontend Build** | `npm run build` | **PASS** | Built in 2.85s (39.20 kB CSS, 314.83 kB JS) |
| **Ruff Linter** | `ruff check .` | **PASS** | 0 violations |
| **Ruff Formatter** | `ruff format --check .` | **PASS** | 383 files formatted cleanly |
| **MyPy Type Checker** | `mypy src tests` | **PASS** | Success: 0 errors in 295 source files |
| **API Endpoints** | `GET /health, /version, /ready` | **PASS** | Correct `FINARQ` metadata returned |
