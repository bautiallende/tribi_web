"""Billing helpers for invoices and sales exports."""

from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import Invoice, Order, Payment
from ..models.auth_models import InvoiceStatus, User


def _generate_invoice_number(order: Order) -> str:
    prefix = settings.INVOICE_PREFIX or "TRB"
    return f"{prefix}-{order.id:06d}"


def generate_invoice_for_order(
    db: Session,
    *,
    order: Order | None,
    payment: Payment | None = None,
) -> Invoice | None:
    """Create an invoice for a paid order if one does not already exist."""

    if not order or not order.id:
        return None

    existing = db.query(Invoice).filter(Invoice.order_id == order.id).one_or_none()
    if existing:
        return existing

    invoice_number = _generate_invoice_number(order)
    currency = order.currency or settings.DEFAULT_CURRENCY

    invoice = Invoice(
        invoice_number=invoice_number,
        order_id=order.id,
        user_id=order.user_id,
        currency=currency,
        amount_minor_units=int(order.amount_minor_units or 0),
        tax_minor_units=0,
        status=InvoiceStatus.ISSUED,
        issued_at=datetime.utcnow(),
        extra_metadata={
            "plan_snapshot": order.plan_snapshot,
            "payment_intent": getattr(payment, "intent_id", None),
        },
    )

    db.add(invoice)
    db.flush()
    return invoice


def build_sales_export_csv(invoices: Iterable[Invoice]) -> io.StringIO:
    """Return a CSV buffer for the provided invoices with normalized columns."""

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "invoice_number",
            "order_id",
            "user_id",
            "user_email",
            "amount_minor_units",
            "tax_minor_units",
            "currency",
            "issued_at",
        ]
    )

    for invoice in invoices:
        user: User | None = getattr(invoice, "user", None)
        email = user.email if user else None
        writer.writerow(
            [
                invoice.invoice_number,
                invoice.order_id,
                invoice.user_id,
                email,
                invoice.amount_minor_units,
                invoice.tax_minor_units,
                invoice.currency,
                invoice.issued_at.isoformat() if invoice.issued_at else None,
            ]
        )

    buffer.seek(0)
    return buffer
