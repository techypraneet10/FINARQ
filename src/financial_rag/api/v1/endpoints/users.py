"""User identity management endpoints with tenant-scoped RBAC."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status

from financial_rag.api.dependencies import (
    AuditServiceDep,
    PasswordHasherDep,
    UserRepoDep,
    require_permission,
)
from financial_rag.api.v1.schemas import (
    CreateUserRequest,
    UpdateUserStatusRequest,
    UserResponse,
)
from financial_rag.domain.entities.security import (
    AuditEvent,
    AuditEventType,
    Permission,
    PrincipalContext,
    User,
    UserStatus,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user within caller's tenant organization",
)
async def create_user(
    request_data: CreateUserRequest,
    user_repo: UserRepoDep,
    hasher: PasswordHasherDep,
    audit_service: AuditServiceDep,
    raw_req: Request,
    principal: PrincipalContext = Depends(require_permission(Permission.USERS_MANAGE)),
) -> UserResponse:
    """Create a new user account under the authenticated administrator's tenant boundary."""
    existing = await user_repo.get_by_email(request_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{request_data.email}' already exists.",
        )

    user_id = str(uuid.uuid4())
    hashed_pwd = hasher.hash_password(request_data.password)

    user = User(
        id=user_id,
        tenant_id=principal.tenant_id,
        email=request_data.email.lower().strip(),
        hashed_password=hashed_pwd,
        role=request_data.role,
        status=UserStatus.ACTIVE,
    )
    saved_user = await user_repo.save(user)

    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.USER_CREATED,
            resource_type="user",
            resource_id=user_id,
            action="create_user",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    return UserResponse.model_validate(saved_user)


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users in caller's tenant organization",
)
async def list_users(
    user_repo: UserRepoDep,
    limit: int = 50,
    offset: int = 0,
    principal: PrincipalContext = Depends(require_permission(Permission.USERS_MANAGE)),
) -> list[UserResponse]:
    """List user identities strictly scoped to the caller's tenant."""
    users = await user_repo.list_by_tenant(
        tenant_id=principal.tenant_id, limit=limit, offset=offset
    )
    return [UserResponse.model_validate(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Retrieve user details within caller's tenant",
)
async def get_user(
    user_id: str,
    user_repo: UserRepoDep,
    principal: PrincipalContext = Depends(require_permission(Permission.USERS_MANAGE)),
) -> UserResponse:
    """Retrieve details for a specific user ID within the caller's tenant organization."""
    user = await user_repo.get_by_id(user_id=user_id, tenant_id=principal.tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Update user status (e.g. disable or suspend account)",
)
async def update_user_status(
    user_id: str,
    request_data: UpdateUserStatusRequest,
    user_repo: UserRepoDep,
    audit_service: AuditServiceDep,
    raw_req: Request,
    principal: PrincipalContext = Depends(require_permission(Permission.USERS_MANAGE)),
) -> UserResponse:
    """Update active status of a user within caller's tenant."""
    user = await user_repo.get_by_id(user_id=user_id, tenant_id=principal.tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found.",
        )

    user.status = request_data.status
    saved = await user_repo.save(user)

    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.USER_DISABLED
            if request_data.status == UserStatus.DISABLED
            else AuditEventType.ROLE_CHANGED,
            resource_type="user",
            resource_id=user_id,
            action="update_status",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
            metadata={"new_status": request_data.status.value},
        )
    )

    return UserResponse.model_validate(saved)
