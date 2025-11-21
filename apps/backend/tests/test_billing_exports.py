from datetime import datetime, timedelta

from app.models import Invoice, Order, User
from app.models.auth_models import InvoiceStatus, OrderStatus
from app.services.billing import generate_invoice_for_order


def _create_user(db_session, email: str = "billing@example.com") -> User:
    user = User(email=email)
    db_session.add(user)
    db_session.flush()
    return user


def _create_order(db_session, user: User, amount_minor: int = 5000) -> Order:
    order = Order(
        user_id=user.id,
        plan_id=1,
        status=OrderStatus.PAID,
        currency="USD",
        amount_minor_units=amount_minor,
        plan_snapshot={"id": 1, "name": "Starter"},
    )
    db_session.add(order)
    db_session.flush()
    return order


def test_generate_invoice_idempotent(db_session):
    user = _create_user(db_session)
    order = _create_order(db_session, user)

    invoice = generate_invoice_for_order(db_session, order=order, payment=None)
    assert invoice is not None
    assert invoice.invoice_number.startswith("TRB-")

    second = generate_invoice_for_order(db_session, order=order, payment=None)
    assert second.id == invoice.id


def test_sales_export_endpoint_returns_csv(client, admin_headers, db_session):
    user = _create_user(db_session, email="export@example.com")
    order = _create_order(db_session, user, amount_minor=7500)

    invoice = Invoice(
        invoice_number="TRB-EXPORT",
        order_id=order.id,
        user_id=user.id,
        currency="USD",
        amount_minor_units=order.amount_minor_units,
        tax_minor_units=0,
        status=InvoiceStatus.ISSUED,
        issued_at=datetime.utcnow() - timedelta(days=1),
    )
    db_session.add(invoice)
    db_session.commit()

    params = {
        "period": "custom",
        "start_date": (datetime.utcnow() - timedelta(days=2)).isoformat(),
        "end_date": datetime.utcnow().isoformat(),
    }

    response = client.get("/admin/exports/sales", params=params, headers=admin_headers)
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"].lower()
    assert "TRB-EXPORT" in response.text
