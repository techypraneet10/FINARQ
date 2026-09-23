# ADR 0036: Immutable Audit Trails & Compliance Logging

## Status
Accepted

## Context
Financial platforms require comprehensive, tamper-evident audit trails documenting all sensitive operations (user creation, login attempts, document uploads, document deletions, role modifications, access policy rejections).

## Decision
We implement a structured, asynchronous audit logging subsystem:

1. **Audit Event Schema**:
   - Every `AuditEvent` records `event_id`, `timestamp`, `tenant_id`, `actor_user_id`, `event_type`, `resource_type`, `resource_id`, `action`, `outcome` (`SUCCESS`, `DENIED`, `ERROR`), `request_id`, `trace_id`, `source_ip`, `user_agent`, and `metadata`.

2. **Sensitive Data Redaction**:
   - `redact_sensitive_dict` and `redact_sensitive_string` sanitize payloads before recording to prevent secret leakage (passwords, tokens, API keys, authorization headers).

3. **Persistence & Isolation**:
   - Audit events are written to the `audit_events` relational table.
   - Retrieval via `/api/v1/audit-events` is strictly isolated by `principal.tenant_id` and requires `Permission.AUDIT_READ`.

## Consequences
### Positive
- Complete auditability for SOC2 / ISO27001 / SEC compliance requirements.
- Zero secret leakage in persistent logs.
