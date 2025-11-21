"""Tests for support automation background jobs."""

from datetime import datetime, timedelta

import pytest
from app.core.config import settings
from app.jobs import tickets as ticket_jobs
from app.models import Order, SupportTicket, User
from app.models.auth_models import (
    OrderStatus,
    SupportTicketPriority,
    SupportTicketStatus,
)

from tests.conftest import TestingSessionLocal


@pytest.fixture(autouse=True)
def patch_job_session(monkeypatch, setup_database):
    """Ensure background jobs use the in-memory test database."""
    monkeypatch.setattr(ticket_jobs, "SessionLocal", TestingSessionLocal)


def _seed_ticket(db_session, *, due_at: datetime) -> SupportTicket:
    user = User(email="jobs-user@tribi.app", name="Jobs User")
    db_session.add(user)
    db_session.flush()

    order = Order(
        user_id=user.id,
        plan_id=1,
        status=OrderStatus.PAID,
        currency="USD",
        amount_minor_units=2099,
    )
    ticket = SupportTicket(
        user_id=user.id,
        order_id=order.id,
        subject="Test ticket",
        priority=SupportTicketPriority.NORMAL,
        status=SupportTicketStatus.OPEN,
        due_at=due_at,
    )
    db_session.add_all([order, ticket])
    db_session.commit()
    return ticket


def test_ticket_reminder_job_updates_fields(db_session):
    now = datetime.utcnow()
    lead_minutes = max(1, settings.SUPPORT_REMINDER_LEAD_MINUTES // 2)
    ticket = _seed_ticket(db_session, due_at=now + timedelta(minutes=lead_minutes))

    stats = ticket_jobs.run_ticket_sla_cycle(now=now)
    assert stats["reminders"] == 1

    db_session.expire_all()
    refreshed = db_session.get(SupportTicket, ticket.id)
    assert refreshed is not None
    assert refreshed.reminder_count == 1
    assert refreshed.last_reminder_at == now
    assert refreshed.audit_entries[-1].event_type.value == "reminder_sent"


def test_ticket_escalation_job_increments_level(db_session):
    now = datetime.utcnow()
    overdue_minutes = settings.SUPPORT_ESCALATION_GRACE_MINUTES * 2
    ticket = _seed_ticket(db_session, due_at=now - timedelta(minutes=overdue_minutes))

    stats = ticket_jobs.run_ticket_sla_cycle(now=now)
    assert stats["escalations"] == 1

    db_session.expire_all()
    refreshed = db_session.get(SupportTicket, ticket.id)
    assert refreshed is not None
    assert refreshed.escalation_level == 1
    assert refreshed.status == SupportTicketStatus.IN_PROGRESS
    assert refreshed.due_at < now
    assert refreshed.audit_entries[-1].event_type.value == "escalated"
