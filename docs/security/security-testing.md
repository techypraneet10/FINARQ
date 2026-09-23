# Financial RAG Platform — Security Testing & Verification Guide

## 1. Security Test Suites

The platform maintains two dedicated automated security test suites:
1. **`tests/integration/test_phase10_security_and_idor.py`**: Foundational authentication error handling, file upload magic bytes validation, path traversal sanitization, and IDOR isolation tests.
2. **`tests/integration/test_phase14_security_hardening.py`**: Comprehensive adversarial security tests covering token tampering, refresh token replay revocation, account lockout, full RBAC privilege boundaries, vector database tenant filtering, indirect prompt injection defense, and security response headers.

---

## 2. Automated Test Execution Commands

### Running Phase 14 Security Tests:
```powershell
.venv\Scripts\pytest tests/integration/test_phase14_security_hardening.py -v
```

### Running Phase 10 Security & IDOR Tests:
```powershell
.venv\Scripts\pytest tests/integration/test_phase10_security_and_idor.py -v
```

### Running Complete Security & Reliability Verification:
```powershell
.venv\Scripts\pytest tests/integration/test_phase14_security_hardening.py tests/integration/test_phase10_security_and_idor.py tests/integration/test_phase13_fault_injection_and_recovery.py -v
```

### Running Static Analysis & Type Checking:
```powershell
.venv\Scripts\ruff check src tests
.venv\Scripts\mypy src
```

---

## 3. Negative Testing Coverage
- **Authentication**: Malformed tokens, unsigned tokens, `"alg": "none"`, expired tokens, wrong secret keys.
- **Refresh Token Replay**: Presenting already-rotated refresh tokens triggering cascade invalidation.
- **Account Lockout**: Exceeding 5 failed logins within 60s triggering HTTP 429 and temporary account lockout.
- **RBAC**: Viewers attempting write/delete, Members attempting user creation, Unauthorized roles attempting audit history queries.
- **IDOR / Multi-Tenancy**: Tenant A requesting Tenant B documents, chunks, versions, jobs, or audit logs.
- **Vector Filtering**: Qdrant search queries with injected foreign tenant IDs.
- **Path Traversal**: Uploads with `../../`, `..\..\`, Windows UNC `\\server\share`, and null byte filenames.
- **File Validation**: Executables disguised as PDFs, 0-byte uploads, oversized files (> 50MB).
- **Prompt Injection**: System override instructions in source evidence and user queries.
