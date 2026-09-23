# Production Financial Workspace & UI Product Layer (Phase 8)

## 1. Executive Summary

Phase 8 completes the Financial RAG Platform by delivering an enterprise-grade, financial-first web workspace built in React 18, TypeScript, and Tailwind/Vanilla Design Tokens.

Unlike generic conversational chatbot interfaces, this platform is purposefully architected to expose the backend's core strengths:
**ANSWER + EVIDENCE + SOURCE + CALCULATION + CONFIDENCE + GROUNDING STATUS**.

---

## 2. Core Architectural Principles

```
+-----------------------------------------------------------------------------+
|                            USER BROWSER / SPA                               |
|   +-------------------+  +--------------------+  +----------------------+   |
|   |   AuthContext     |  |  WorkspaceContext  |  |     ThemeContext     |   |
|   +---------+---------+  +---------+----------+  +----------+-----------+   |
|             |                      |                        |               |
|   +---------v----------------------v------------------------v-----------+   |
|   |                       Typed API Client                              |   |
|   |     (Token Lifecycle, X-Request-ID, 401 Refresh, Error Envelope)    |   |
|   +--------------------------------+------------------------------------+   |
+------------------------------------|----------------------------------------+
                                     | JSON / Multipart over HTTP/2
+------------------------------------v----------------------------------------+
|                          BACKEND FASTAPI GATEWAY                            |
|   /api/v1/auth    /api/v1/documents    /api/v1/retrieval    /api/v1/reasoning
+-----------------------------------------------------------------------------+
```

### 2.1 The Evidence & Provenance Axiom
Every number presented in an answer is treated as a verifiable claim tied directly to an immutable source chunk in an SEC filing. 

1. **Interactive Citation Badges `[C1]`**:
   Clicking any inline citation tag opens the **Evidence Drawer**, navigating the analyst to the exact Document ID, Immutable Version, Page Number, Section Hierarchy (`Part II > Item 8`), and Bounding Box coordinates.
2. **Deterministic Arithmetic Visualizer**:
   Mathematical formulas (YoY growth rates, margin expansions, operating ratio comparisons) are displayed with exact decimal arithmetic, operand fact links, and precision rounding.
3. **Contradiction Resolution & Precedence**:
   When filings contain conflicting numbers (e.g. rounded text narrative vs audited financial statement table), the platform highlights both numbers and explains the table-first precedence rationale.
4. **Zero Hallucination Guarantee**:
   When documents do not contain authoritative evidence, the platform returns an explicit **Insufficient Evidence** card detailing missing facts rather than guessing.

---

## 3. Component Architecture & Design System

### 3.1 Design System Tokens (`frontend/src/design-system/`)
- `Button.tsx`: Variants (`primary`, `emerald`, `secondary`, `danger`, `outline`, `ghost`), loading spinner, accessibility rings.
- `Input.tsx`: Floating labels, icons, error badges, helper texts.
- `Select.tsx`: Custom chevron selector with keyboard accessibility.
- `Badge.tsx`: Monospace tabular badge with color variants (`emerald`, `amber`, `rose`, `purple`, `cyan`, `slate`).
- `Card.tsx`: Glassmorphism gradient surface with header, badge, and footer slots.
- `Modal.tsx`: Accessible dialog with ESC key traps and backdrop blur.
- `Drawer.tsx`: Slide-in side panel with smooth spring animation.
- `Table.tsx`: Financial table with accounting cell alignment and sticky headers.
- `StatusBadge.tsx`: Canonical indicators for Ingestion, Grounding, and Answerability.
- `Progress.tsx`: Multi-stage pipeline progress indicator.
- `Alert.tsx`: Dismissible alerts for errors, warnings, and success notifications.

### 3.2 Feature Views (`frontend/src/components/`)
- **Dashboard (`DashboardView.tsx`)**: Executive workspace overview with quick stats, recent SEC filings, and suggested financial analysis prompts.
- **Document Management (`DocumentListView.tsx`, `DocumentDetailView.tsx`, `DocumentUploadModal.tsx`)**: Paginated document library, drag-and-drop PDF ingestion, page inspection, chunk inspection, and version tracking.
- **Source Reader & Bounding Boxes (`DocumentViewer.tsx`, `BoundingBoxOverlay.tsx`, `FinancialTableViewer.tsx`)**: Multi-page document reader with SVG coordinate box overlays, structured table viewer, and PDF streaming.
- **Hybrid Search (`SearchView.tsx`, `SearchFilters.tsx`, `RankedEvidenceCard.tsx`)**: Dense vector + BM25 keyword search with Reciprocal Rank Fusion transparency and metadata filtering.
- **Question & Verification Workspace (`AskView.tsx`, `QuestionComposer.tsx`, `AnswerPackageView.tsx`, `CalculationBlock.tsx`, `ClaimList.tsx`, `ConflictResolutionCard.tsx`)**: Core financial intelligence synthesis workspace.
- **Research Library (`SavedAnalysesView.tsx`)**: Saved research reports with Markdown and JSON exports.
- **Ingestion Pipeline (`IngestionJobsView.tsx`, `IngestionProgressTracker.tsx`)**: Real-time tracker of OCR, table extraction, normalization, chunking, and embedding stages.
- **Administration & Security (`AdminView.tsx`, `UserManagement.tsx`, `AuditLogViewer.tsx`)**: RBAC user provisioning and immutable audit trails.
- **System Observability (`SystemMetricsView.tsx`)**: Live downstream dependency readiness checks and performance telemetry counters.

---

## 4. Security & Cryptographic Multi-Tenant Isolation

1. **Tenant-Scoped State & Token Rotation**:
   JWT access tokens (15-minute TTL) are rotated transparently via refresh tokens. Switching tenants purges local caches immediately to prevent cross-tenant state leakage.
2. **Role-Based Permission Enforcement**:
   - `OWNER`: Full organization control, user provisioning, document deletion, and audit inspection.
   - `ADMIN`: User management and ingestion pipeline retry.
   - `MEMBER`: Document upload, retrieval, and reasoning queries.
   - `VIEWER`: Read-only access to search and question answering.
3. **Hardened Nginx Container**:
   Protected with strict Content Security Policy (CSP), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, gzip compression, and asset caching.

---

## 5. Development & Deployment

### Local Frontend Development
```bash
cd frontend
npm install
npm run dev
# Running on http://localhost:5173 with proxy to http://127.0.0.1:8000
```

### Production Build & Test
```bash
cd frontend
npm run build
npm test -- --run
```

### Docker Compose Stack
```bash
docker compose up --build
```
Access the application at `http://localhost:5173`.
