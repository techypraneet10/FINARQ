"""Centralized Role-Based Access Control and Tenant Boundary Authorization Service."""

from financial_rag.domain.entities.security import Permission, PrincipalContext
from financial_rag.domain.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TenantIsolationError,
)
from financial_rag.domain.interfaces.security import AuthorizationServiceProtocol
from financial_rag.infrastructure.logging import get_logger

logger = get_logger("financial_rag.infrastructure.security.authorization")


class RbacAuthorizationService(AuthorizationServiceProtocol):
    """Centralized authorization decision point enforcing RBAC permissions and strict tenant isolation."""

    def check_permission(self, principal: PrincipalContext, permission: Permission) -> None:
        """Assert that the principal is authenticated and has the required permission."""
        if not principal.is_authenticated:
            raise AuthenticationError(message="Authentication required to perform this action.")

        if principal.is_platform_admin:
            return

        if not principal.has_permission(permission):
            logger.warning(
                f"Authorization denied for user '{principal.user_id}' (tenant='{principal.tenant_id}', role='{principal.role.value}'). Missing permission: '{permission.value}'"
            )
            raise AuthorizationError(
                message=f"Principal lacks required permission: '{permission.value}'",
                code="FORBIDDEN",
                details={
                    "user_id": principal.user_id,
                    "tenant_id": principal.tenant_id,
                    "role": principal.role.value,
                    "required_permission": permission.value,
                },
            )

    def can_access(
        self,
        principal: PrincipalContext,
        resource_tenant_id: str,
        permission: Permission | None = None,
    ) -> bool:
        """Evaluate whether a principal is allowed access without raising exceptions."""
        if not principal.is_authenticated:
            return False

        if not principal.is_platform_admin and principal.tenant_id != resource_tenant_id:
            return False

        if permission is not None:
            return principal.has_permission(permission)

        return True

    def enforce_tenant_access(
        self,
        principal: PrincipalContext,
        resource_tenant_id: str,
        resource_id: str | None = None,
    ) -> None:
        """Enforce strict tenant boundary: principal tenant MUST equal resource tenant."""
        if not principal.is_authenticated:
            raise AuthenticationError(message="Authentication required.")

        if principal.is_platform_admin:
            return

        if principal.tenant_id != resource_tenant_id:
            logger.warning(
                f"Cross-tenant access attempted by user '{principal.user_id}' (tenant='{principal.tenant_id}') targeting resource '{resource_id}' in tenant '{resource_tenant_id}'."
            )
            raise TenantIsolationError(
                resource_tenant_id=resource_tenant_id,
                principal_tenant_id=principal.tenant_id,
                resource_id=resource_id,
            )

    def has_permission(self, principal: PrincipalContext, permission: Permission) -> bool:
        """Check if principal has permission."""
        return principal.has_permission(permission)

    def check_tenant_access(self, principal: PrincipalContext, resource_tenant_id: str) -> bool:
        """Enforce tenant access, raising TenantIsolationError on mismatch, and return True on success."""
        self.enforce_tenant_access(principal, resource_tenant_id)
        return True
