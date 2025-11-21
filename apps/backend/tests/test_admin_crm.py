"""Tests covering CRM admin endpoints."""

from datetime import datetime, timedelta

from app.models import Order, SupportTicket, User
from app.models.auth_models import (
    OrderStatus,
    SupportTicketPriority,
    SupportTicketStatus,
)


def _seed_user(db_session, email: str = "crm-user@tribi.app"):
    user = User(email=email, name="CRM User")
    db_session.add(user)
    db_session.flush()

    order = Order(
        user_id=user.id,
        plan_id=1,
        status=OrderStatus.PAID,
        currency="USD",
        amount_minor_units=1099,
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(user)
    db_session.refresh(order)
    return user, order


def test_admin_users_list_includes_metrics(client, admin_headers, db_session):
    user, order = _seed_user(db_session)

    ticket = SupportTicket(
        user_id=user.id,
        order_id=order.id,
        subject="Need help activating",
        description="eSIM fails to download",
        priority=SupportTicketPriority.HIGH,
    )
    db_session.add(ticket)
    db_session.commit()

    response = client.get("/admin/users", headers=admin_headers)
    assert response.status_code == 200

    payload = response.json()
    assert payload["total"] >= 1

    match = next(item for item in payload["items"] if item["id"] == user.id)
    assert match["total_orders"] == 1
    assert match["total_spent_minor_units"] == 1099
    assert match["open_tickets"] == 1


def test_admin_update_user_notes(client, admin_headers, db_session):
    user, _ = _seed_user(db_session)

    payload = {"internal_notes": "VIP traveler prefers WhatsApp"}
    response = client.patch(
        f"/admin/users/{user.id}/notes",
        json=payload,
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["internal_notes"] == payload["internal_notes"]


def test_support_ticket_lifecycle(client, admin_headers, db_session):
    user, order = _seed_user(db_session)

    create_payload = {
        "user_id": user.id,
        "order_id": order.id,
        "subject": "Device cannot detect eSIM",
        "description": "Customer stuck on activation screen",
        "priority": "high",
    }
    create_resp = client.post(
        "/admin/support/tickets",
        json=create_payload,
        headers=admin_headers,
    )
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["status"] == SupportTicketStatus.OPEN.value
    assert created["due_at"] is not None
    assert created["audits"], "creation audit missing"
    assert created["audits"][0]["event_type"] == "created"

    patch_payload = {
        "status": "resolved",
        "internal_notes": "Reset profile; customer confirmed fix",
    }
    update_resp = client.patch(
        f"/admin/support/tickets/{created['id']}",
        json=patch_payload,
        headers=admin_headers,
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["status"] == SupportTicketStatus.RESOLVED.value
    assert updated["internal_notes"] == patch_payload["internal_notes"]
    assert updated["resolved_at"] is not None
    status_events = [
        a for a in updated["audits"] if a["event_type"] == "status_changed"
    ]
    assert status_events, "status change audit missing"

    list_resp = client.get("/admin/support/tickets", headers=admin_headers)
    assert list_resp.status_code == 200
    ids = [ticket["id"] for ticket in list_resp.json()["items"]]
    assert created["id"] in ids


def test_support_ticket_due_override_records_audit(client, admin_headers, db_session):
    user, order = _seed_user(db_session)

    resp = client.post(
        "/admin/support/tickets",
        json={
            "user_id": user.id,
            "order_id": order.id,
            "subject": "Need refund",
            "priority": "normal",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    ticket = resp.json()

    new_due = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    patch_resp = client.patch(
        f"/admin/support/tickets/{ticket['id']}",
        json={"due_at": new_due, "internal_notes": "requested quicker follow-up"},
        headers=admin_headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["due_at"].startswith(new_due[:16])

    sla_events = [a for a in updated["audits"] if a["event_type"] == "sla_updated"]
    assert sla_events, "SLA update audit missing"
    assert sla_events[-1]["metadata"]["reason"] == "manual_override"


def test_support_ticket_priority_boost_recomputes_sla(
    client, admin_headers, db_session
):
    user, order = _seed_user(db_session)

    resp = client.post(
        "/admin/support/tickets",
        json={
            "user_id": user.id,
            "order_id": order.id,
            "subject": "Slow data",
            "priority": "normal",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    ticket = resp.json()
    original_due = datetime.fromisoformat(ticket["due_at"])

    patch_resp = client.patch(
        f"/admin/support/tickets/{ticket['id']}",
        json={"priority": "high"},
        headers=admin_headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    new_due = datetime.fromisoformat(updated["due_at"])
    assert new_due < original_due

    sla_events = [a for a in updated["audits"] if a["event_type"] == "sla_updated"]
    assert sla_events, "Expected SLA update after priority change"
    assert sla_events[-1]["metadata"]["reason"] == "priority_changed"
