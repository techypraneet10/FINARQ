"""Unit tests for audit logging and redaction."""

import pytest

from financial_rag.domain.entities.security import AuditEvent, AuditEventType
from financial_rag.infrastructure.security.audit import AuditService
from financial_rag.infrastructure.security.redaction import (
    redact_sensitive_dict,
    redact_sensitive_string,
)


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def save(self, event: AuditEvent) -> AuditEvent:
        self.events.append(event)
        return event

    async def list_by_tenant(
        self, tenant_id: str, limit: int = 100, offset: int = 0
    ) -> list[AuditEvent]:
        return [e for e in self.events if e.tenant_id == tenant_id][offset : offset + limit]


@pytest.mark.asyncio
async def test_audit_event_logging_and_enrichment() -> None:
    repo = InMemoryAuditRepository()
    service = AuditService(audit_repository=repo)

    event = AuditEvent(
        tenant_id="tenant-123",
        actor_user_id="user-456",
        event_type=AuditEventType.DOCUMENT_CREATED,
        resource_type="document",
        resource_id="doc-789",
        action="upload",
        outcome="SUCCESS",
        metadata={"filename": "10k.pdf", "password": "supersecretpassword"},
    )

    saved = await service.log_event(event)
    assert saved.event_id is not None
    assert saved.metadata["password"] == "[REDACTED]"

    events = await service.list_events(tenant_id="tenant-123")
    assert len(events) == 1
    assert events[0].resource_id == "doc-789"


def test_redaction_utilities() -> None:
    assert redact_sensitive_string("Bearer eyJhbGciOi...") == "Bearer [REDACTED]"
    data = {
        "user": "alice",
        "password": "secret",
        "api_key": "12345",
        "nested": {"token": "abc"},
    }
    redacted = redact_sensitive_dict(data)
    assert redacted["user"] == "alice"
    assert redacted["password"] == "[REDACTED]"
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["token"] == "[REDACTED]"
