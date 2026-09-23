"""Domain interfaces and protocol contracts for Security, Authentication, and Multi-Tenancy."""

from typing import Any, Protocol, runtime_checkable

from financial_rag.domain.entities.security import (
    AuditEvent,
    Permission,
    PrincipalContext,
    RefreshToken,
    Tenant,
    User,
    UserRole,
)


@runtime_checkable
class PasswordHasherProtocol(Protocol):
    """Protocol for secure, memory-hard password hashing and verification."""

    def hash_password(self, plain_password: str) -> str:
        """Hash a plaintext password with a random cryptographically secure salt."""
        ...

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a stored hashed credential in constant time."""
        ...


@runtime_checkable
class TokenManagerProtocol(Protocol):
    """Protocol for signing, issuing, verifying, and decoding JWT access and refresh tokens."""

    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        role: UserRole,
        expires_in_minutes: int | None = None,
        custom_claims: dict[str, Any] | None = None,
    ) -> str:
        """Issue a short-lived, signed JWT access token."""
        ...

    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        expires_in_days: int | None = None,
    ) -> tuple[str, str, str]:
        """Issue a long-lived refresh token. Returns (raw_token, token_id, token_hash)."""
        ...

    def verify_access_token(self, token: str) -> dict[str, Any]:
        """Validate an access token's signature, algorithm, issuer, audience, and expiration."""
        ...

    def verify_refresh_token(self, token: str) -> dict[str, Any]:
        """Validate a refresh token's signature and claims."""
        ...


@runtime_checkable
class AuthorizationServiceProtocol(Protocol):
    """Centralized authorization decision point for RBAC and tenant boundaries."""

    def check_permission(self, principal: PrincipalContext, permission: Permission) -> None:
        """Assert that the principal has the given permission, raising AuthorizationError if not."""
        ...

    def can_access(
        self,
        principal: PrincipalContext,
        resource_tenant_id: str,
        permission: Permission | None = None,
    ) -> bool:
        """Evaluate if the principal is authorized to access a tenant-owned resource."""
        ...

    def enforce_tenant_access(
        self,
        principal: PrincipalContext,
        resource_tenant_id: str,
        resource_id: str | None = None,
    ) -> None:
        """Assert that resource belongs to principal's tenant, raising TenantIsolationError if not."""
        ...


@runtime_checkable
class RateLimiterProtocol(Protocol):
    """Protocol for sliding-window and token-bucket API rate limiting."""

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> tuple[bool, int, float]:
        """Check rate limit for a key. Returns (is_allowed, remaining_requests, retry_after_seconds)."""
        ...

    def record_failed_login(self, identifier: str) -> int:
        """Record a failed login attempt for brute force throttling."""
        ...

    def reset_failed_logins(self, identifier: str) -> None:
        """Reset failed login count upon successful authentication."""
        ...

    def is_locked_out(self, identifier: str) -> tuple[bool, float]:
        """Check if an account or IP is temporarily locked out."""
        ...


@runtime_checkable
class AuditLoggerProtocol(Protocol):
    """Protocol for logging immutable security and compliance audit events."""

    async def log_event(self, event: AuditEvent) -> AuditEvent:
        """Record an audit event."""
        ...

    async def list_events(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit history for a specific tenant."""
        ...


@runtime_checkable
class TenantRepositoryProtocol(Protocol):
    """Repository contract for Tenant organization persistence."""

    async def save(self, tenant: Tenant) -> Tenant:
        """Persist or update tenant entity."""
        ...

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        """Retrieve tenant by its ID."""
        ...

    async def list_tenants(self, limit: int = 50, offset: int = 0) -> list[Tenant]:
        """List all tenants."""
        ...


@runtime_checkable
class UserRepositoryProtocol(Protocol):
    """Repository contract for User identity persistence."""

    async def save(self, user: User) -> User:
        """Persist or update user entity."""
        ...

    async def get_by_id(self, user_id: str, tenant_id: str | None = None) -> User | None:
        """Retrieve user by ID, optionally scoped to tenant."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve user by email address across or within tenant."""
        ...

    async def list_by_tenant(self, tenant_id: str, limit: int = 50, offset: int = 0) -> list[User]:
        """List users belonging to a specific tenant."""
        ...


@runtime_checkable
class RefreshTokenRepositoryProtocol(Protocol):
    """Repository contract for RefreshToken persistence and revocation."""

    async def save(self, token: RefreshToken) -> RefreshToken:
        """Persist a refresh token record."""
        ...

    async def get_by_id(self, token_id: str) -> RefreshToken | None:
        """Retrieve token record by ID."""
        ...

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Retrieve token record by its SHA-256 hash."""
        ...

    async def revoke_token(self, token_id: str, rotated_to_id: str | None = None) -> bool:
        """Mark a specific refresh token as revoked."""
        ...

    async def revoke_all_for_user(self, user_id: str) -> int:
        """Revoke all active refresh tokens for a user upon logout or credential reset."""
        ...


@runtime_checkable
class AuditEventRepositoryProtocol(Protocol):
    """Repository contract for AuditEvent append-only storage."""

    async def save(self, event: AuditEvent) -> AuditEvent:
        """Append an audit event record."""
        ...

    async def list_by_tenant(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """List audit events for a tenant ordered by timestamp descending."""
        ...
