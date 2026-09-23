# Financial RAG Platform — Authorization & RBAC Model

## 1. Principle of Least Privilege
Authorization answers: *"What is the authenticated principal allowed to perform on which specific resource within which tenant boundary?"*

Frontend UI guards are non-authoritative. The backend FastAPI application independently derives and enforces all permissions.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Permission | Description | VIEWER | MEMBER | ADMIN | OWNER |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `documents:read` | View document metadata, versions, extracted pages, chunks, and download PDF binaries | ✓ | ✓ | ✓ | ✓ |
| `documents:write` | Upload new financial documents and trigger ingestion | ✗ | ✓ | ✓ | ✓ |
| `documents:delete` | Delete documents, extracted artifacts, and vector index records | ✗ | ✗ | ✓ | ✓ |
| `documents:share` | Share document collections across internal teams | ✗ | ✗ | ✓ | ✓ |
| `ingestion:read` | View background ingestion job status, progress, and stage diagnostics | ✓ | ✓ | ✓ | ✓ |
| `ingestion:retry` | Trigger retry on failed ingestion jobs | ✗ | ✓ | ✓ | ✓ |
| `retrieval:execute`| Execute hybrid search, reranking, and evidence extraction | ✓ | ✓ | ✓ | ✓ |
| `answers:execute` | Request verified natural language answer synthesis and streaming | ✓ | ✓ | ✓ | ✓ |
| `tenant:manage` | Manage tenant organization settings, billing, and global configuration | ✗ | ✗ | ✗ | ✓ |
| `users:manage` | Create, list, disable, or modify user accounts in tenant | ✗ | ✗ | ✓ | ✓ |
| `audit:read` | Query immutable security and operational audit event records | ✗ | ✗ | ✓ | ✓ |

---

## 3. Enforcement Mechanisms

### Route Guard Dependency: `require_permission`
```python
@router.post("/documents")
async def upload_document(
    ...,
    principal: PrincipalContext = Depends(require_permission(Permission.DOCUMENTS_WRITE)),
):
    ...
```

### Object-Level Authorization (IDOR / BOLA Prevention)
All resource access routes (`/documents/{id}`, `/ingestion-jobs/{id}`, `/users/{id}`) pass the verified `principal.tenant_id` down to the service and repository queries. If a document or job does not belong to the caller's tenant:
- Return `HTTP 404 Not Found` (avoids disclosing existence of foreign resources).
- Asynchronously record an `UNAUTHORIZED_ACCESS_ATTEMPT` audit event.
