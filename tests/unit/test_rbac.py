"""Unit tests for Role-Based Access Control and tenant boundaries."""

import pytest

from financial_rag.domain.entities.security import (
    ROLE_PERMISSIONS,
    Permission,
    PrincipalContext,
    UserRole,
)
from financial_rag.domain.exceptions import AuthorizationError, TenantIsolationError
from financial_rag.infrastructure.security.authorization import RbacAuthorizationService


def test_owner_has_all_permissions() -> None:
    service = RbacAuthorizationService()
    owner = PrincipalContext(
        user_id="owner-1",
        tenant_id="tenant-alpha",
        role=UserRole.OWNER,
        permissions=ROLE_PERMISSIONS[UserRole.OWNER],
    )

    for perm in Permission:
        assert service.has_permission(owner, perm) is True
        service.check_permission(owner, perm)  # Should not raise


def test_viewer_restricted_permissions() -> None:
    service = RbacAuthorizationService()
    viewer = PrincipalContext(
        user_id="viewer-1",
        tenant_id="tenant-alpha",
        role=UserRole.VIEWER,
        permissions=ROLE_PERMISSIONS[UserRole.VIEWER],
    )

    assert service.has_permission(viewer, Permission.DOCUMENTS_READ) is True
    assert service.has_permission(viewer, Permission.DOCUMENTS_WRITE) is False
    assert service.has_permission(viewer, Permission.DOCUMENTS_DELETE) is False
    assert service.has_permission(viewer, Permission.USERS_MANAGE) is False

    with pytest.raises(AuthorizationError):
        service.check_permission(viewer, Permission.DOCUMENTS_WRITE)


def test_cross_tenant_access_isolation() -> None:
    service = RbacAuthorizationService()
    principal = PrincipalContext(
        user_id="user-1",
        tenant_id="tenant-alpha",
        role=UserRole.ADMIN,
        permissions=ROLE_PERMISSIONS[UserRole.ADMIN],
    )

    # Access within own tenant
    assert service.check_tenant_access(principal, "tenant-alpha") is True

    # Access across tenants must raise TenantIsolationError
    with pytest.raises(TenantIsolationError):
        service.check_tenant_access(principal, "tenant-beta")
