"""Audit log history endpoints with tenant isolation."""

from fastapi import APIRouter, Depends

from financial_rag.api.dependencies import AuditServiceDep, require_permission
from financial_rag.api.v1.schemas import AuditEventResponse
from financial_rag.domain.entities.security import Permission, PrincipalContext

router = APIRouter(prefix="/audit-events", tags=["Audit"])


@router.get(
    "",
    response_model=list[AuditEventResponse],
    summary="Query audit history for caller's tenant organization",
)
async def list_audit_events(
    audit_service: AuditServiceDep,
    limit: int = 50,
    offset: int = 0,
    principal: PrincipalContext = Depends(require_permission(Permission.AUDIT_READ)),
) -> list[AuditEventResponse]:
    """Retrieve immutable audit records strictly scoped to the authenticated caller's tenant."""
    events = await audit_service.list_events(
        tenant_id=principal.tenant_id, limit=limit, offset=offset
    )
    return [AuditEventResponse.model_validate(ev) for ev in events]
