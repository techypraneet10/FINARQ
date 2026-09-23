"""Audit logging service for security events, access tracking, and compliance."""

from financial_rag.domain.entities.security import AuditEvent
from financial_rag.domain.interfaces.security import (
    AuditEventRepositoryProtocol,
    AuditLoggerProtocol,
)
from financial_rag.infrastructure.logging import (
    get_logger,
    request_id_ctx_var,
)
from financial_rag.infrastructure.observability.tracer import trace_id_ctx_var
from financial_rag.infrastructure.security.redaction import redact_sensitive_dict

logger = get_logger("financial_rag.infrastructure.security.audit")


class AuditService(AuditLoggerProtocol):
    """Authoritative audit service managing append-only security and compliance trails."""

    def __init__(self, audit_repository: AuditEventRepositoryProtocol | None = None) -> None:
        self._repository = audit_repository

    async def log_event(self, event: AuditEvent) -> AuditEvent:
        """Record an audit event, enriching with contextual request and trace identifiers."""
        req_id = event.request_id or request_id_ctx_var.get()
        tr_id = event.trace_id or trace_id_ctx_var.get()
        cleaned_meta = redact_sensitive_dict(event.metadata) if event.metadata else {}

        enriched_event = AuditEvent(
            event_id=event.event_id,
            timestamp=event.timestamp,
            tenant_id=event.tenant_id,
            actor_user_id=event.actor_user_id,
            event_type=event.event_type,
            resource_type=event.resource_type,
            resource_id=event.resource_id,
            action=event.action,
            outcome=event.outcome,
            request_id=req_id,
            trace_id=tr_id,
            source_ip=event.source_ip,
            user_agent=event.user_agent,
            metadata=cleaned_meta,
        )

        logger.info(
            f"[AUDIT] {enriched_event.event_type.value} | tenant={enriched_event.tenant_id} | "
            f"user={enriched_event.actor_user_id} | resource={enriched_event.resource_type}:{enriched_event.resource_id} | "
            f"action={enriched_event.action} | outcome={enriched_event.outcome}"
        )

        if self._repository:
            await self._repository.save(enriched_event)

        return enriched_event

    async def list_events(
        self,
        tenant_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEvent]:
        """Query audit history for a specific tenant."""
        if not self._repository:
            return []
        return await self._repository.list_by_tenant(
            tenant_id=tenant_id, limit=limit, offset=offset
        )
