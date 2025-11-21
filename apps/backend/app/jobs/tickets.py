"""Ticket-focused background jobs (reminders, escalations, digests)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Literal, cast

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from ..core.config import settings
from ..db.session import SessionLocal
from ..models.auth_models import (
    SupportTicket,
    SupportTicketEventType,
    SupportTicketStatus,
)
from ..services.support import get_support_automation_service

logger = logging.getLogger(__name__)
_system_actor = "system:scheduler"
support_automation = get_support_automation_service()


def run_ticket_sla_cycle(now: datetime | None = None) -> dict[str, int]:
    """Entry point used by the async scheduler to run the SLA workflow."""
    now = now or datetime.utcnow()
    with SessionLocal() as db:
        stats = process_ticket_sla(db, now)
        db.commit()
        return stats


def run_support_digest(
    now: datetime | None = None,
    *,
    cadence: Literal["daily", "weekly"] = "daily",
) -> dict[str, int]:
    """Log digest metrics for support health."""
    now = now or datetime.utcnow()
    with SessionLocal() as db:
        metrics = _collect_support_metrics(db, now, cadence)
        logger.info("Support %s digest", cadence, extra={"metrics": metrics})
        return metrics


def process_ticket_sla(db: Session, now: datetime) -> dict[str, int]:
    reminders = _send_ticket_reminders(db, now)
    escalations = _escalate_overdue_tickets(db, now)
    return {"reminders": reminders, "escalations": escalations}


def _open_statuses() -> list[SupportTicketStatus]:
    return [SupportTicketStatus.OPEN, SupportTicketStatus.IN_PROGRESS]


def _send_ticket_reminders(db: Session, now: datetime) -> int:
    reminder_window = now + timedelta(minutes=settings.SUPPORT_REMINDER_LEAD_MINUTES)
    reminder_interval = timedelta(minutes=settings.SUPPORT_REMINDER_INTERVAL_MINUTES)

    candidates = (
        db.query(SupportTicket)
        .options(joinedload(SupportTicket.user))
        .filter(
            SupportTicket.status.in_(_open_statuses()),
            SupportTicket.due_at.isnot(None),
            SupportTicket.due_at <= reminder_window,
            or_(
                SupportTicket.last_reminder_at.is_(None),
                SupportTicket.last_reminder_at <= (now - reminder_interval),
            ),
        )
        .all()
    )

    sent = 0
    for ticket in candidates:
        due_at = cast(datetime | None, ticket.due_at)
        current_count = int(getattr(ticket, "reminder_count") or 0) + 1
        setattr(ticket, "last_reminder_at", now)
        setattr(ticket, "reminder_count", current_count)
        metadata = {
            "due_at": due_at.isoformat() if due_at is not None else None,
            "reminder_count": current_count,
        }
        logger.info(
            "Reminder sent for ticket %s (user %s)",
            ticket.id,
            ticket.user_id,
            extra={"metadata": metadata},
        )
        support_automation.record_audit(
            db,
            ticket,
            event_type=SupportTicketEventType.REMINDER_SENT,
            actor=_system_actor,
            metadata=metadata,
        )
        sent += 1

    return sent


def _escalate_overdue_tickets(db: Session, now: datetime) -> int:
    grace = timedelta(minutes=settings.SUPPORT_ESCALATION_GRACE_MINUTES)
    candidates = (
        db.query(SupportTicket)
        .options(joinedload(SupportTicket.user))
        .filter(
            SupportTicket.status.in_(_open_statuses()),
            SupportTicket.due_at.isnot(None),
            SupportTicket.due_at <= now,
        )
        .all()
    )

    escalations = 0
    for ticket in candidates:
        current_level = int(getattr(ticket, "escalation_level") or 0)
        if current_level >= settings.SUPPORT_MAX_ESCALATION_LEVEL:
            continue
        due_at = cast(datetime | None, ticket.due_at)
        if due_at is None:
            continue
        next_threshold = due_at + grace * (current_level + 1)
        if now < next_threshold:
            continue

        new_level = current_level + 1
        current_status = cast(SupportTicketStatus, ticket.status)
        new_status = current_status
        if current_status == SupportTicketStatus.OPEN:
            new_status = SupportTicketStatus.IN_PROGRESS
            setattr(ticket, "status", new_status)
        setattr(ticket, "escalation_level", new_level)
        metadata = {
            "level": new_level,
            "due_at": due_at.isoformat(),
        }
        logger.warning(
            "Escalated ticket %s to level %s",
            ticket.id,
            new_level,
            extra={"metadata": metadata},
        )
        support_automation.record_audit(
            db,
            ticket,
            event_type=SupportTicketEventType.ESCALATED,
            actor=_system_actor,
            metadata=metadata,
            from_status=current_status,
            to_status=new_status,
        )
        escalations += 1

    return escalations


def _collect_support_metrics(
    db: Session, now: datetime, cadence: Literal["daily", "weekly"]
) -> dict[str, int]:
    open_total = (
        db.query(func.count(SupportTicket.id))
        .filter(SupportTicket.status.in_(_open_statuses()))
        .scalar()
        or 0
    )
    overdue_total = (
        db.query(func.count(SupportTicket.id))
        .filter(
            SupportTicket.status.in_(_open_statuses()),
            SupportTicket.due_at.isnot(None),
            SupportTicket.due_at < now,
        )
        .scalar()
        or 0
    )

    window = timedelta(days=1 if cadence == "daily" else 7)
    reminders_sent = (
        db.query(func.count(SupportTicket.id))
        .filter(
            SupportTicket.last_reminder_at.isnot(None),
            SupportTicket.last_reminder_at >= (now - window),
        )
        .scalar()
        or 0
    )

    return {
        "open_tickets": int(open_total),
        "overdue_tickets": int(overdue_total),
        "recent_reminders": int(reminders_sent),
    }
