"""Seed database with comprehensive dummy data for manual testing."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from ..db.session import SessionLocal
from ..models import (
    Country,
    EsimInventory,
    EsimProfile,
    Order,
    Payment,
    Plan,
    User,
)
from ..models.auth_models import (
    EsimInventoryStatus,
    EsimStatus,
    OrderStatus,
    PaymentProvider,
    PaymentStatus,
)
from ..seed.seed import seed_database
from ..services.pricing import to_minor_units


def _ensure_core_seed_data(session: Session) -> None:
    """Seed countries/carriers/plans if database is empty."""
    if session.query(Country).count() == 0 or session.query(Plan).count() == 0:
        seed_database()


def _get_or_create_user(session: Session, email: str, name: str) -> User:
    user = session.query(User).filter(User.email == email).first()
    if user:
        return user
    user = User(email=email, name=name)
    session.add(user)
    session.flush()
    return user


def _build_plan_snapshot(plan: Plan, currency: str) -> dict:
    price = Decimal(plan.price_usd or 0)
    amount_minor = to_minor_units(price)
    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "country_id": plan.country_id,
        "carrier_id": plan.carrier_id,
        "country_name": plan.country.name if plan.country else None,
        "carrier_name": plan.carrier.name if plan.carrier else None,
        "data_gb": float(plan.data_gb or 0),
        "duration_days": plan.duration_days,
        "price_minor_units": amount_minor,
        "currency": currency,
    }


def _ensure_inventory_for_plan(
    session: Session, plan: Plan, target_count: int = 25
) -> None:
    existing = (
        session.query(EsimInventory).filter(EsimInventory.plan_id == plan.id).count()
    )
    to_create = max(0, target_count - existing)
    if to_create == 0:
        return
    for offset in range(to_create):
        serial = existing + offset + 1
        activation_code = f"SEED-{plan.id}-{serial:04d}"
        inventory = EsimInventory(
            plan_id=plan.id,
            carrier_id=plan.carrier_id,
            country_id=plan.country_id,
            activation_code=activation_code,
            iccid=f"89001{plan.id:05d}{serial:09d}",
            qr_payload=f"LPA:1${activation_code}",
            status=EsimInventoryStatus.AVAILABLE,
            provider_reference=f"SEED-{activation_code}",
        )
        session.add(inventory)


def _attach_inventory_item(session: Session, plan: Plan) -> EsimInventory | None:
    item = (
        session.query(EsimInventory)
        .filter(
            EsimInventory.plan_id == plan.id,
            EsimInventory.status == EsimInventoryStatus.AVAILABLE,
        )
        .first()
    )
    if not item:
        return None
    item.status = EsimInventoryStatus.ASSIGNED
    now = datetime.utcnow()
    item.reserved_at = item.reserved_at or now
    item.assigned_at = now
    return item


def _seed_orders_for_user(session: Session, user: User, plans: list[Plan]) -> None:
    if not plans:
        return

    status_cycle = [
        OrderStatus.CREATED,
        OrderStatus.PAID,
        OrderStatus.FAILED,
        OrderStatus.PAID,
        OrderStatus.REFUNDED,
    ]

    for idx, plan in enumerate(plans):
        idempotency_key = f"seed:{user.email}:{plan.id}:{idx}"
        existing = (
            session.query(Order)
            .filter(Order.idempotency_key == idempotency_key)
            .one_or_none()
        )
        if existing:
            continue

        currency = "USD"
        plan_snapshot = _build_plan_snapshot(plan, currency)
        amount_minor = int(plan_snapshot.get("price_minor_units", 0))
        status = status_cycle[idx % len(status_cycle)]

        order = Order(
            user_id=user.id,
            plan_id=plan.id,
            status=status,
            currency=currency,
            amount_minor_units=amount_minor,
            idempotency_key=idempotency_key,
            plan_snapshot=plan_snapshot,
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 20)),
        )
        session.add(order)
        session.flush()

        esim_status = EsimStatus.PENDING_ACTIVATION
        inventory_item = None
        if status in {OrderStatus.PAID, OrderStatus.REFUNDED}:
            inventory_item = _attach_inventory_item(session, plan)
            esim_status = EsimStatus.ASSIGNED if inventory_item else EsimStatus.RESERVED
        elif status == OrderStatus.FAILED:
            esim_status = EsimStatus.FAILED

        esim_profile = EsimProfile(
            order_id=order.id,
            user_id=user.id,
            plan_id=plan.id,
            country_id=plan.country_id,
            carrier_id=plan.carrier_id,
            status=esim_status,
            activation_code=(
                inventory_item.activation_code
                if inventory_item
                else f"PENDING-{order.id}"
            ),
            iccid=inventory_item.iccid if inventory_item else None,
            qr_payload=inventory_item.qr_payload if inventory_item else None,
            inventory_item_id=inventory_item.id if inventory_item else None,
            created_at=order.created_at,
        )
        session.add(esim_profile)

        if status in {OrderStatus.PAID, OrderStatus.REFUNDED, OrderStatus.FAILED}:
            payment_status = (
                PaymentStatus.SUCCEEDED
                if status in {OrderStatus.PAID, OrderStatus.REFUNDED}
                else PaymentStatus.FAILED
            )
            payment = Payment(
                order_id=order.id,
                provider=PaymentProvider.MOCK,
                status=payment_status,
                intent_id=f"seed_intent_{order.id}",
                created_at=order.created_at + timedelta(minutes=5),
            )
            session.add(payment)


def seed_sample_data() -> None:
    session = SessionLocal()
    try:
        _ensure_core_seed_data(session)

        plans = session.query(Plan).order_by(Plan.id).limit(10).all()
        if not plans:
            raise RuntimeError("No plans available to seed sample data")

        for plan in plans:
            _ensure_inventory_for_plan(session, plan)

        users = [
            _get_or_create_user(session, "demo+alice@tribi.app", "Alice Demo"),
            _get_or_create_user(session, "demo+bob@tribi.app", "Bob Demo"),
            _get_or_create_user(session, "demo+carol@tribi.app", "Carol Demo"),
        ]

        for user in users:
            _seed_orders_for_user(session, user, plans[:5])

        session.commit()
        print("✅ Sample data seeded successfully.")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_sample_data()
