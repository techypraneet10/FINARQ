"""Domain entities, value objects, and enums for Security, Identity, and Multi-Tenancy."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    """Return current UTC timestamp."""
    return datetime.now(UTC)


class TenantStatus(StrEnum):
    """Lifecycle status of a tenant account."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class UserStatus(StrEnum):
    """Lifecycle status of a user identity."""

    ACTIVE = "active"
    DISABLED = "disabled"
    SUSPENDED = "suspended"
    PENDING = "pending"


class UserRole(StrEnum):
    """Role categories for Role-Based Access Control."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(StrEnum):
    """Discrete, granular actions that can be authorized."""

    DOCUMENTS_READ = "documents:read"
    DOCUMENTS_WRITE = "documents:write"
    DOCUMENTS_DELETE = "documents:delete"
    DOCUMENTS_SHARE = "documents:share"
    INGESTION_READ = "ingestion:read"
    INGESTION_RETRY = "ingestion:retry"
    RETRIEVAL_EXECUTE = "retrieval:execute"
    ANSWERS_EXECUTE = "answers:execute"
    TENANT_MANAGE = "tenant:manage"
    USERS_MANAGE = "users:manage"
    AUDIT_READ = "audit:read"


# Authoritative role-to-permission mapping matrix
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.OWNER: {
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_WRITE,
        Permission.DOCUMENTS_DELETE,
        Permission.DOCUMENTS_SHARE,
        Permission.INGESTION_READ,
        Permission.INGESTION_RETRY,
        Permission.RETRIEVAL_EXECUTE,
        Permission.ANSWERS_EXECUTE,
        Permission.TENANT_MANAGE,
        Permission.USERS_MANAGE,
        Permission.AUDIT_READ,
    },
    UserRole.ADMIN: {
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_WRITE,
        Permission.DOCUMENTS_DELETE,
        Permission.DOCUMENTS_SHARE,
        Permission.INGESTION_READ,
        Permission.INGESTION_RETRY,
        Permission.RETRIEVAL_EXECUTE,
        Permission.ANSWERS_EXECUTE,
        Permission.USERS_MANAGE,
        Permission.AUDIT_READ,
    },
    UserRole.MEMBER: {
        Permission.DOCUMENTS_READ,
        Permission.DOCUMENTS_WRITE,
        Permission.INGESTION_READ,
        Permission.RETRIEVAL_EXECUTE,
        Permission.ANSWERS_EXECUTE,
    },
    UserRole.VIEWER: {
        Permission.DOCUMENTS_READ,
        Permission.INGESTION_READ,
        Permission.RETRIEVAL_EXECUTE,
        Permission.ANSWERS_EXECUTE,
    },
}


@dataclass
class Tenant:
    """Tenant organization boundary entity."""

    id: str
    name: str
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class User:
    """User account entity within a tenant boundary."""

    id: str
    tenant_id: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.MEMBER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    last_login_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PrincipalContext:
    """Server-derived trusted context representing the authenticated caller."""

    user_id: str
    tenant_id: str
    role: UserRole
    permissions: set[Permission]
    authentication_method: str = "bearer_jwt"
    is_authenticated: bool = True
    is_platform_admin: bool = False

    def has_permission(self, permission: Permission) -> bool:
        """Check if the principal possesses a specific permission."""
        if self.is_platform_admin:
            return True
        return permission in self.permissions


@dataclass
class RefreshToken:
    """Persistent refresh token record for token rotation and revocation."""

    token_id: str
    user_id: str
    tenant_id: str
    token_hash: str
    expires_at: datetime
    revoked: bool = False
    created_at: datetime = field(default_factory=utc_now)
    rotated_to_token_id: str | None = None


class AuditEventType(StrEnum):
    """Categorical types of security and operational audit events."""

    USER_LOGIN_SUCCESS = "USER_LOGIN_SUCCESS"
    USER_LOGIN_FAILURE = "USER_LOGIN_FAILURE"
    USER_LOGOUT = "USER_LOGOUT"
    TOKEN_REFRESH = "TOKEN_REFRESH"
    USER_CREATED = "USER_CREATED"
    USER_DISABLED = "USER_DISABLED"
    ROLE_CHANGED = "ROLE_CHANGED"
    TENANT_CREATED = "TENANT_CREATED"
    TENANT_SUSPENDED = "TENANT_SUSPENDED"
    DOCUMENT_CREATED = "DOCUMENT_CREATED"
    DOCUMENT_ACCESSED = "DOCUMENT_ACCESSED"
    DOCUMENT_DELETED = "DOCUMENT_DELETED"
    INGESTION_RETRIED = "INGESTION_RETRIED"
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    CROSS_TENANT_ACCESS_ATTEMPT = "CROSS_TENANT_ACCESS_ATTEMPT"
    RATE_LIMIT_TRIGGERED = "RATE_LIMIT_TRIGGERED"
    SECURITY_CONFIGURATION_CHANGED = "SECURITY_CONFIGURATION_CHANGED"


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit trail record for tracking security events."""

    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=utc_now)
    tenant_id: str | None = None
    actor_user_id: str | None = None
    event_type: AuditEventType = AuditEventType.DOCUMENT_ACCESSED
    resource_type: str = "document"
    resource_id: str | None = None
    action: str = "read"
    outcome: str = "SUCCESS"  # "SUCCESS", "DENIED", "FAILURE"
    request_id: str | None = None
    trace_id: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
