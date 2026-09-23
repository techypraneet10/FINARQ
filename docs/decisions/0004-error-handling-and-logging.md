# 4. Error Handling and Structured Logging

Date: 2026-08-20  
Status: Accepted

## Context
High-reliability financial document systems require comprehensive traceability, audit logging, and consistent error response contracts across all API endpoints.

## Decision
1. **Error Hierarchy**: We define a unified base exception `FinancialRAGError` with categorical subclasses (`DomainError`, `ConfigurationError`, `InfrastructureError`, `NotFoundError`, `ValidationError`, `ExternalServiceError`).
2. **Standard Error Envelopes**: Global FastAPI exception handlers convert internal exceptions into standard JSON error objects containing error `code`, `message`, `details`, and `request_id`.
3. **Structured Logging**: We implement a logging foundation with JSON formatting for production and human-readable text formatting for development. Inbound requests generate an `X-Request-ID` correlation ID stored in Python `contextvars` and automatically attached to all log records.

## Consequences
### Positive
- Consistent API error responses adhering to RFC 7807 principles.
- End-to-end correlation between HTTP requests, log entries, and error reports.
- No sensitive internal stack traces leaked to API consumers.

### Negative / Trade-offs
- Developers must use custom domain exceptions rather than raising arbitrary built-in errors.
