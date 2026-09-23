"""Authentication and session management API endpoints."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status

from financial_rag.api.dependencies import (
    AuditServiceDep,
    JwtManagerDep,
    PasswordHasherDep,
    PrincipalDep,
    RefreshTokenRepoDep,
    SettingsDep,
    TenantRepoDep,
    UserRepoDep,
)
from financial_rag.api.middleware import get_rate_limiter
from financial_rag.api.v1.schemas import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from financial_rag.domain.entities.security import (
    ROLE_PERMISSIONS,
    AuditEvent,
    AuditEventType,
    RefreshToken,
    Tenant,
    TenantStatus,
    User,
    UserStatus,
)
from financial_rag.domain.exceptions import SecurityError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user and tenant organization",
)
async def register(
    request_data: RegisterRequest,
    tenant_repo: TenantRepoDep,
    user_repo: UserRepoDep,
    refresh_token_repo: RefreshTokenRepoDep,
    hasher: PasswordHasherDep,
    jwt_manager: JwtManagerDep,
    audit_service: AuditServiceDep,
    settings: SettingsDep,
    raw_req: Request,
) -> TokenResponse:
    """Register a new user identity and initialize their isolated tenant organization."""
    # Check if user email already exists
    existing = await user_repo.get_by_email(request_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{request_data.email}' already exists.",
        )

    # Create new tenant
    tenant_id = str(uuid.uuid4())
    tenant_name = request_data.tenant_name or f"Tenant-{request_data.email.split('@')[0]}"
    tenant = Tenant(
        id=tenant_id,
        name=tenant_name,
        status=TenantStatus.ACTIVE,
    )
    await tenant_repo.save(tenant)

    # Hash password with memory-hard scrypt
    hashed_pwd = hasher.hash_password(request_data.password)

    # Create user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        email=request_data.email.lower().strip(),
        hashed_password=hashed_pwd,
        role=request_data.role,
        status=UserStatus.ACTIVE,
        last_login_at=datetime.now(UTC),
    )
    await user_repo.save(user)

    # Issue JWT tokens
    access_token = jwt_manager.create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )
    raw_refresh, jti, token_hash = jwt_manager.create_refresh_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    # Persist refresh token
    refresh_ttl_days = settings.security.refresh_token_ttl_days
    refresh_rec = RefreshToken(
        token_id=jti,
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=refresh_ttl_days),
    )
    await refresh_token_repo.save(refresh_rec)

    # Audit log registration
    await audit_service.log_event(
        AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            event_type=AuditEventType.USER_CREATED,
            resource_type="user",
            resource_id=user_id,
            action="register",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    perms = [p.value for p in ROLE_PERMISSIONS.get(user.role, set())]
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in_seconds=settings.security.access_token_ttl_minutes * 60,
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
        permissions=perms,
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate with email and password",
)
async def login(
    request_data: LoginRequest,
    user_repo: UserRepoDep,
    tenant_repo: TenantRepoDep,
    refresh_token_repo: RefreshTokenRepoDep,
    hasher: PasswordHasherDep,
    jwt_manager: JwtManagerDep,
    audit_service: AuditServiceDep,
    settings: SettingsDep,
    raw_req: Request,
) -> TokenResponse:
    """Authenticate credentials, check lockout, and issue fresh access/refresh token pair."""
    limiter = get_rate_limiter()
    client_ip = raw_req.client.host if raw_req.client else "127.0.0.1"
    login_id = f"{client_ip}:{request_data.email.lower().strip()}"

    # Check brute force lockout
    is_locked, retry_after = limiter.is_locked_out(login_id)
    if is_locked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts. Account temporarily locked. Retry after {retry_after:.1f}s.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )

    user = await user_repo.get_by_email(request_data.email)
    if not user:
        limiter.record_failed_login(login_id)
        await audit_service.log_event(
            AuditEvent(
                event_type=AuditEventType.USER_LOGIN_FAILURE,
                resource_type="auth",
                action="login",
                outcome="DENIED",
                source_ip=client_ip,
                user_agent=raw_req.headers.get("user-agent"),
                metadata={"email": request_data.email, "reason": "user_not_found"},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check password verification
    if not hasher.verify_password(request_data.password, user.hashed_password):
        limiter.record_failed_login(login_id)
        await audit_service.log_event(
            AuditEvent(
                tenant_id=user.tenant_id,
                actor_user_id=user.id,
                event_type=AuditEventType.USER_LOGIN_FAILURE,
                resource_type="auth",
                action="login",
                outcome="DENIED",
                source_ip=client_ip,
                user_agent=raw_req.headers.get("user-agent"),
                metadata={"email": request_data.email, "reason": "invalid_credentials"},
            )
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user and tenant status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is suspended or disabled.",
        )

    tenant = await tenant_repo.get_by_id(user.tenant_id)
    if not tenant or tenant.status != TenantStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant organization account is suspended or disabled.",
        )

    # Success: reset failed logins
    limiter.reset_failed_logins(login_id)

    # Update last login timestamp
    user.last_login_at = datetime.now(UTC)
    await user_repo.save(user)

    # Issue JWT tokens
    access_token = jwt_manager.create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )
    raw_refresh, jti, token_hash = jwt_manager.create_refresh_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    # Persist refresh token
    refresh_rec = RefreshToken(
        token_id=jti,
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.security.refresh_token_ttl_days),
    )
    await refresh_token_repo.save(refresh_rec)

    # Audit log login
    await audit_service.log_event(
        AuditEvent(
            tenant_id=user.tenant_id,
            actor_user_id=user.id,
            event_type=AuditEventType.USER_LOGIN_SUCCESS,
            resource_type="auth",
            action="login",
            outcome="SUCCESS",
            source_ip=client_ip,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    perms = [p.value for p in ROLE_PERMISSIONS.get(user.role, set())]
    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in_seconds=settings.security.access_token_ttl_minutes * 60,
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
        permissions=perms,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and issue new access token",
)
async def refresh_tokens(
    request_data: RefreshTokenRequest,
    refresh_token_repo: RefreshTokenRepoDep,
    user_repo: UserRepoDep,
    jwt_manager: JwtManagerDep,
    audit_service: AuditServiceDep,
    settings: SettingsDep,
    raw_req: Request,
) -> TokenResponse:
    """Validate refresh token, revoke previous token, rotate, and issue new tokens."""
    try:
        claims = jwt_manager.verify_refresh_token(request_data.refresh_token)
    except SecurityError as ex:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(ex.message),
            headers={"WWW-Authenticate": "Bearer"},
        ) from ex

    jti = claims["jti"]
    user_id = claims["sub"]
    tenant_id = claims["tid"]

    # Verify refresh token in database
    token_rec = await refresh_token_repo.get_by_id(jti)
    if not token_rec or token_rec.revoked:
        # Possible token reuse attack: revoke all tokens for this user
        if token_rec and token_rec.revoked:
            await refresh_token_repo.revoke_all_for_user(user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked or is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch active user
    user = await user_repo.get_by_id(user_id=user_id, tenant_id=tenant_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive or disabled.",
        )

    # Issue new token pair
    new_access = jwt_manager.create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )
    new_refresh, new_jti, new_hash = jwt_manager.create_refresh_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
    )

    # Revoke old refresh token with pointer to rotated token
    await refresh_token_repo.revoke_token(token_id=jti, rotated_to_id=new_jti)

    # Persist new refresh token
    new_rec = RefreshToken(
        token_id=new_jti,
        user_id=user.id,
        tenant_id=user.tenant_id,
        token_hash=new_hash,
        expires_at=datetime.now(UTC) + timedelta(days=settings.security.refresh_token_ttl_days),
    )
    await refresh_token_repo.save(new_rec)

    # Audit log token refresh
    await audit_service.log_event(
        AuditEvent(
            tenant_id=tenant_id,
            actor_user_id=user_id,
            event_type=AuditEventType.TOKEN_REFRESH,
            resource_type="auth",
            action="refresh",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    perms = [p.value for p in ROLE_PERMISSIONS.get(user.role, set())]
    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in_seconds=settings.security.access_token_ttl_minutes * 60,
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role.value,
        permissions=perms,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active user refresh tokens and terminate session",
)
async def logout(
    principal: PrincipalDep,
    refresh_token_repo: RefreshTokenRepoDep,
    audit_service: AuditServiceDep,
    raw_req: Request,
) -> dict[str, Any]:
    """Revoke all active refresh tokens for the authenticated user."""
    revoked_count = await refresh_token_repo.revoke_all_for_user(principal.user_id)

    await audit_service.log_event(
        AuditEvent(
            tenant_id=principal.tenant_id,
            actor_user_id=principal.user_id,
            event_type=AuditEventType.USER_LOGOUT,
            resource_type="auth",
            action="logout",
            outcome="SUCCESS",
            source_ip=raw_req.client.host if raw_req.client else None,
            user_agent=raw_req.headers.get("user-agent"),
        )
    )

    return {"message": "Successfully logged out.", "tokens_revoked": revoked_count}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current authenticated user profile",
)
async def get_me(
    principal: PrincipalDep,
    user_repo: UserRepoDep,
) -> UserResponse:
    """Return identity details of the authenticated caller."""
    user = await user_repo.get_by_id(principal.user_id, tenant_id=principal.tenant_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Authenticated user profile not found.",
        )
    return UserResponse.model_validate(user)
