"""Support automation helpers for SLA tracking and audit logging."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.auth_models import (
    SupportTicket,
    SupportTicketAudit,
    SupportTicketEventType,
    SupportTicketPriority,
    SupportTicketStatus,
)


class SupportAutomationService:
    """Encapsulates SLA calculations and audit utilities for tickets."""

    def __init__(self) -> None:
        self._sla_map: dict[SupportTicketPriority, int] = {
            SupportTicketPriority.LOW: settings.SUPPORT_SLA_HOURS_LOW,
            SupportTicketPriority.NORMAL: settings.SUPPORT_SLA_HOURS_NORMAL,
            SupportTicketPriority.HIGH: settings.SUPPORT_SLA_HOURS_HIGH,
        }

    def sla_hours_for_priority(self, priority: SupportTicketPriority) -> int:
        return self._sla_map.get(priority, settings.SUPPORT_SLA_HOURS_NORMAL)

    def compute_due_at(
        self,
        ticket: SupportTicket,
        *,
        created_at: datetime | None = None,
        due_override: datetime | None = None,
    ) -> datetime:
        if due_override:
            return due_override

        base = created_at or ticket.created_at or datetime.utcnow()
        hours = self.sla_hours_for_priority(ticket.priority)
        return base + timedelta(hours=hours)

    def ensure_due_at(
        self,
        ticket: SupportTicket,
        *,
        due_override: datetime | None = None,
    ) -> datetime:
        due_at = self.compute_due_at(ticket, due_override=due_override)
        ticket.due_at = due_at
        return due_at

    def record_audit(
        self,
        db: Session,
        ticket: SupportTicket,
        *,
        event_type: SupportTicketEventType,
        actor: str | None,
        notes: str | None = None,
        metadata: dict[str, Any] | None = None,
        from_status: SupportTicketStatus | None = None,
        to_status: SupportTicketStatus | None = None,
    ) -> SupportTicketAudit:
        audit_entry = SupportTicketAudit(
            ticket_id=ticket.id,
            event_type=event_type,
            actor=actor,
            from_status=from_status,
            to_status=to_status,
            notes=notes,
            extra_metadata=metadata,
        )
        db.add(audit_entry)
        ticket.updated_at = datetime.utcnow()
        return audit_entry


def get_support_automation_service() -> SupportAutomationService:
    return SupportAutomationService()
