# FINARQ — Financial Document Intelligence & Verified Reasoning Platform
## UI/UX Visual Redesign & Design System Specification

---

### Executive Summary

**Product Name:** `FINARQ` (formerly `VERIDEX`)  
**Tagline:** `Financial Document Intelligence & Verified Reasoning Platform`  
**Design Philosophy:** Dark-first, minimal, premium, compact, data-dense, calm, precise, and professional enterprise research terminal.

---

### 1. Current UI Root Cause Analysis

Prior to this visual remediation, the web application presented an unstyled HTML appearance:
1. **Missing PostCSS Compilation Pipeline:**  
   The React components utilized Tailwind CSS utility classes, but `package.json` lacked `tailwindcss`, `postcss`, and `autoprefixer`, and no `tailwind.config.js` / `postcss.config.js` files existed. Vite compiled `index.css` as a raw 156-line stylesheet (2.73 kB) with zero generated utility classes.
2. **Generic Error Bubble-Up:**  
   Unseeded or 500 error responses from the backend surfaced directly as raw `"Internal Server Error"` alerts without correlation request IDs, diagnostic context, or guided retry mechanisms.
3. **Fragmented Visual Tokens:**  
   The application shell lacked a unified design system with compact financial density, monospace tabular formatting, and dedicated verification status tokens.

---

### 2. Design Direction

FINARQ delivers the visual authority and density of a financial terminal (e.g. Bloomberg / FactSet meets modern workspace intelligence):
- **Surface Hierarchy:** Deep obsidian backgrounds (`#07090e`), subtle slate panels (`#0d101a`), and low-contrast borders (`#1a1f30`).
- **Restrained Accents:**
  - Primary Brand / Action: Restrained Violet/Purple (`#8b5cf6`, `#7c3aed`).
  - Verification & Grounding: Emerald (`#10b981`).
  - Signal / Latency Metrics: Cyan (`#06b6d4`).
  - Warnings: Amber (`#f59e0b`).
  - Errors & Negative Values: Rose/Red (`#f43f5e`).
- **Typography & Numeral Formatting:**
  - Interface Typography: `Inter` sans-serif with strict scale (10px, 11px, 12px, 14px, 16px).
  - Financial Arithmetic & Numbers: `JetBrains Mono` with `font-variant-numeric: tabular-nums lining-nums` for strict decimal alignment and accounting negatives (e.g. `($210,352)`).

---

### 3. Design Tokens

| Token Category | CSS / Utility Value | Hex / Spec | Usage |
|---|---|---|---|
| **Background (Primary)** | `bg-slate-950` | `#07090e` | Canvas background |
| **Background (Surface)** | `bg-slate-900` | `#0d101a` | Card & panel containers |
| **Background (Elevated)** | `bg-slate-850` | `#141824` | Table headers, inputs, chips |
| **Border (Subtle)** | `border-slate-800` | `#1a1f30` | Structural card borders |
| **Border (Highlight)** | `border-purple-500/40` | `rgba(139, 92, 246, 0.4)` | Active focus & selection |
| **Brand Accent** | `text-purple-400` / `bg-purple-600` | `#8b5cf6` | Primary CTAs, active nav items |
| **Verification Accent** | `text-emerald-400` / `bg-emerald-950` | `#10b981` | Grounded claims, citations |
| **Monospace Numeral** | `font-mono-num` | `JetBrains Mono` | Tabular numbers & calculations |

---

### 4. Application Shell

The desktop workspace shell consists of:
- **Compact Top Bar (14 / 56px height):**
  - Left: Organization boundary (`Org: tenant-b8a91c20`), role badge (`Lead Analyst`), and quick search trigger (`Ctrl+K`).
  - Right: "Upload Filing" CTA, downstream readiness probe status pill (`SYSTEM READY ●`), dark/light theme switch, and analyst profile menu.
- **Persistent Sidebar (60 / 240px width):**
  - Brand Header: `FINARQ` geometric verification prism mark with live pulse indicator.
  - Three distinct navigation groups:
    1. **WORKSPACE:** `Overview`, `Documents`, `Search`, `Ask FINARQ`, `Research Library`.
    2. **OPERATIONS:** `Ingestion Jobs`, `System Metrics`.
    3. **GOVERNANCE:** `Administration`, `Settings`.
  - Trust Footer: Deterministic pipeline assurance badge.

---

### 5. Dashboard (`DashboardView.tsx`)

The financial intelligence dashboard provides:
1. **Welcome Header:** Personalized greeting with workspace status.
2. **Compact 5-Tile Key Metric Row:**
   - Documents Indexed (`128`)
   - Verified Answers (`342`)
   - Grounding Coverage (`98.7%`)
   - Vector Chunks (`840`)
   - Pipeline Uptime (`99.9%`, 18.4ms p95)
3. **Analytics Activity Grid:**
   - Monthly Document Ingestion activity sparkline curve.
   - Weekly Research Query Volume bar pattern across days of the week.
   - Verification Integrity scorecard (Grounded: 98.7%, Precision: 100%, AST Accuracy: 100%, Unsupported: 0%).
4. **Recent Filings Repository Table:**
   - Displays ticker chips, company names, filing types (10-K, 10-Q), fiscal periods, status pills, and one-click inspect actions.
5. **Suggested Queries & Operational Probes Bar:**
   - Pre-populated financial queries for instant verification.
   - Downstream health monitors (Postgres, Qdrant, S3 Blob).

---

### 6. Ask FINARQ Workspace (`AskView.tsx` & `AnswerPackageView.tsx`)

1. **Question Composer:**
   - Multi-line financial query input with keyboard shortcuts (`Enter` to submit, `Shift+Enter` for newline).
   - Response style selector (`Concise`, `Standard`, `Detailed`, `Analytical`).
   - Retrieval scope drawer for ticker and filing type filtering.
2. **Primary Verified Answer Card:**
   - Prominent status header: `✓ GROUNDED` · `✓ CALCULATION VERIFIED` · `✓ SOURCES AUDITED`.
   - Analytical answer text containing interactive emerald citation pills `[C1]`, `[C2]`.
   - Confidence score gauge and one-click "Save Analysis" action.
3. **Deterministic Calculation Card (`CalculationBlock.tsx`):**
   - Renders exact mathematical formula, step-by-step arithmetic in monospace tabular format, and interactive input operand chips linking directly to ground truth facts.
4. **Extracted Facts Table:**
   - Expandable table detailing metric name, currency-formatted numerical value, fiscal period, source ticker, and page number.
5. **Atomic Claim Verification List (`ClaimList.tsx`):**
   - Granular breakdown of individual claims with verification status and citation badges.

---

### 7. Evidence & Citation UX (`EvidenceDrawer.tsx` & `SourceInspector.tsx`)

- Clicking any `[C1]` / `[C2]` citation tag or fact link opens the slide-in **Evidence Drawer**.
- Displays authoritative document metadata (Document ID, Version, Ticker, Fiscal Period, Page Number).
- Excerpts the exact cited passage with highlighted search keywords and bounding box coordinates (`[ymin, xmin, ymax, xmax]`).
- Includes a direct "Open Document in Reader" navigation trigger.

---

### 8. Document Repository & Reader (`DocumentListView.tsx` & `DocumentViewer.tsx`)

- **Repository List:**
  - Filterable by ticker, filing type (10-K, 10-Q, 8-K), and full-text keyword match.
  - Displays SHA-256 integrity hashes, page counts, chunk counts, and creation timestamps.
- **Upload Filing Modal:**
  - Drag-and-drop file upload with progress tracking and metadata tagging.
- **Document Reader (`DocumentViewer.tsx`):**
  - Multi-page reader with page navigation controls.
  - Multi-layer Bounding Box Overlay highlighting cited blocks.
  - Structured Financial Table Viewer (`FinancialTableViewer.tsx`) supporting column alignments, negative accounting formats (`($210,352)` in rose text), and CSV export.

---

### 9. Search Terminal (`SearchView.tsx`)

- Multi-vector hybrid search engine combining dense semantic search (Qdrant) and lexical keyword matching (BM25).
- Ranked evidence cards with dense/sparse score breakdowns, reciprocal rank fusion (RRF) metrics, and quick "Ask FINARQ about this excerpt" action.

---

### 10. Operations & Governance UX

- **Ingestion Pipeline (`IngestionJobsView.tsx` & `IngestionProgressTracker.tsx`):**
  - Real-time 8-stage visual pipeline tracker: `Upload` &rarr; `Parse` &rarr; `OCR` &rarr; `Tables` &rarr; `Normalize` &rarr; `Chunk` &rarr; `Embed` &rarr; `Index` &rarr; `Complete`.
  - Stage elapsed duration, error diagnostic drawer, and one-click retry trigger.
- **Research Library (`SavedAnalysesView.tsx`):**
  - Pinned reports with JSON and Markdown export functionality.
- **Administration (`AdminView.tsx` & `UserManagement.tsx`):**
  - RBAC user directory with role assignment (`Owner`, `Admin`, `Member`, `Viewer`).
  - Immutable audit trail timeline (`AuditLogViewer.tsx`).
- **System Observability (`SystemMetricsView.tsx`):**
  - Prometheus metrics histograms, p95/p99 query latencies, and circuit breaker health gauges.

---

### 11. Responsive Design

- **Desktop (&ge; 1024px):** Persistent compact sidebar, multi-column dashboard, split answer and evidence layouts.
- **Tablet (768px - 1023px):** Responsive icon sidebar, auto-wrapping metrics grid.
- **Mobile (< 768px):** Single-column stacked layouts, full-width overlay drawer for citations, horizontally scrollable financial tables.

---

### 12. Accessibility

- WCAG AAA contrast ratio for text on dark backgrounds.
- Explicit focus rings: `:focus-visible { outline: 2px solid #8b5cf6; outline-offset: 2px; }`.
- Screen-reader accessible ARIA labels on all icon buttons, modals, and drawers.
- Semantic HTML tags (`<main>`, `<header>`, `<aside>`, `<nav>`, `<table>`).

---

### 13. API Error Handling & Diagnostics

- All API errors are translated into structured, user-friendly diagnostic cards via `ApiClientError`.
- Generic `500 Internal Server Error` strings are replaced with actionable explanations and correlation Request IDs (`X-Request-ID: req_xxxx`).
- Single-click retry and quick test identity switchers prevent dead-ends.

---

### 14. Verification & Testing Summary

1. **Frontend Unit & Component Tests:**
   ```bash
   cd frontend && npm test -- --run
   # Output: 4 test files passed, 21 tests passed cleanly in 3.14s
   ```
2. **Frontend Production Build:**
   ```bash
   cd frontend && npm run build
   # Output: built in 2.83s, 39.20 kB CSS bundle, 314.87 kB JS bundle
   ```
3. **Backend Regression Test Suite:**
   ```bash
   .venv\Scripts\python.exe -m pytest tests/
   # Output: 353 passed in 80.62s
   ```
4. **Code Quality & Typing:**
   ```bash
   .venv\Scripts\python.exe scripts/lint.py
   # Output: Ruff 0 violations, Ruff format 381 files clean, MyPy 0 errors in 295 source files
   ```

---

### 16. Authentication Integration & Root Cause Resolution

1. **Root Cause:**
   - Unreachable standalone PostgreSQL port 5432 in local development defaulted `DatabaseSettings` to a refused TCP socket, returning HTTP 500.
   - Quick test personas (`tenant_a@financial.org` and `tenant_b@financial.org`) were not seeded into the database schema.
2. **Resolution:**
   - Configured `.env` to use asynchronous SQLite (`sqlite+aiosqlite:///./data/financial_rag_dev.db`) in local development.
   - Added automated startup seeding in `main.py` lifespan for `tenant-alpha` and `tenant-beta` with `scrypt` password hashing (`Password123!`).
   - Verified that both Tenant A and Tenant B authenticate, receive signed JWT tokens, access their isolated workspaces, and can log out cleanly.

---

### 17. Final File Inventory

#### Files Created
- `.env`
- `frontend/src/components/brand/Logo.tsx`
- `frontend/tailwind.config.js`
- `frontend/postcss.config.js`
- `docs/veridex-ui-redesign.md`

#### Files Modified
- `frontend/package.json`
- `frontend/index.html`
- `frontend/src/styles/index.css`
- `frontend/src/api/client.ts`
- `frontend/src/design-system/Button.tsx`
- `frontend/src/components/layout/Sidebar.tsx`
- `frontend/src/components/layout/Header.tsx`
- `frontend/src/components/layout/AppLayout.tsx`
- `frontend/src/components/auth/LoginForm.tsx`
- `frontend/src/components/auth/RegisterForm.tsx`
- `frontend/src/components/dashboard/QuickStats.tsx`
- `frontend/src/components/dashboard/DashboardView.tsx`
- `frontend/src/components/ask/QuestionComposer.tsx`
- `frontend/src/components/__tests__/auth_and_routing.test.tsx`
- `src/financial_rag/main.py`

#### Key Preserved Architecture & Domain Files (Untouched)
- `src/financial_rag/domain/*` (All AST mathematical reasoning, citations, domain entities)
- `src/financial_rag/infrastructure/retrieval/*` (Hybrid search, Qdrant vector engine, BM25)
- `src/financial_rag/infrastructure/evaluation/*` (Reasoning evaluator, failure attribution)
- `src/financial_rag/infrastructure/reliability/*` (Fault injection, circuit breakers, fallback)
- `src/financial_rag/infrastructure/security/*` (Cryptographic verification, RBAC, tenant isolation)
- `tests/*` (All 353 unit and integration tests)
