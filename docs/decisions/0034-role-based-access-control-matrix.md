# ADR 0034: Granular Role-Based Access Control (RBAC) Matrix

## Status
Accepted

## Context
Different users within a tenant organization hold varying degrees of operational responsibility (e.g. read-only analysts, data managers, tenant administrators, organization owners). The system must enforce least privilege access across 11 granular permission boundaries.

## Decision
We define 4 distinct user roles (`OWNER`, `ADMIN`, `MEMBER`, `VIEWER`) mapping to 11 atomic permissions:

| Permission | OWNER | ADMIN | MEMBER | VIEWER |
| :--- | :---: | :---: | :---: | :---: |
| `documents:read` | Yes | Yes | Yes | Yes |
| `documents:write` | Yes | Yes | Yes | No |
| `documents:delete` | Yes | Yes | No | No |
| `ingestion:read` | Yes | Yes | Yes | Yes |
| `ingestion:retry` | Yes | Yes | No | No |
| `retrieval:execute`| Yes | Yes | Yes | Yes |
| `answers:execute` | Yes | Yes | Yes | Yes |
| `users:manage` | Yes | Yes | No | No |
| `audit:read` | Yes | Yes | No | No |
| `settings:manage` | Yes | Yes | No | No |
| `tenant:manage` | Yes | No | No | No |

1. **Permission Enforcement**:
   - Endpoints specify required permissions via `require_permission(Permission.xyz)` dependency.
   - `RbacAuthorizationService` validates principal context against role definition before executing business logic.
   - `AUTHENTICATED != AUTHORIZED`: Authentication succeeds if credentials are valid; authorization requires specific permission and matching tenant ID.

## Consequences
### Positive
- Strict principle of least privilege.
- Clear separation between administration, data management, and read-only consumption.
