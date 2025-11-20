"""Tests for advanced admin management endpoints (orders, payments, inventory)."""

from decimal import Decimal

import pytest
from app.models import (
    Carrier,
    Country,
    EsimInventory,
    EsimProfile,
    Order,
    Payment,
    Plan,
    User,
)
from app.models.auth_models import (
    EsimInventoryStatus,
    EsimStatus,
    OrderStatus,
    PaymentProvider,
    PaymentStatus,
)

pytestmark = pytest.mark.usefixtures("cleanup_seed_data")


def _create_plan(
    db_session, iso2: str = "AR", carrier_name: str = "Test Carrier"
) -> Plan:
    country = Country(iso2=iso2, name=f"Country {iso2}")
    carrier = Carrier(name=carrier_name)
    plan = Plan(
        name=f"Plan {iso2}",
        country=country,
        carrier=carrier,
        data_gb=Decimal("5"),
        duration_days=7,
        price_usd=Decimal("10.00"),
        description="Test plan",
        is_unlimited=False,
    )
    db_session.add_all([country, carrier, plan])
    db_session.commit()
    db_session.refresh(plan)
    return plan


def _create_user(db_session, email: str = "user@example.com") -> User:
    user = User(email=email, name="Test User")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _create_order(
    db_session,
    user: User,
    plan: Plan,
    status: OrderStatus = OrderStatus.PAID,
    amount_minor_units: int = 1000,
) -> Order:
    order = Order(
        user_id=user.id,
        plan_id=plan.id,
        status=status,
        currency="USD",
        amount_minor_units=amount_minor_units,
        plan_snapshot={"id": plan.id, "name": plan.name},
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order


def _add_payment(
    db_session,
    order: Order,
    provider: PaymentProvider = PaymentProvider.STRIPE,
    status: PaymentStatus = PaymentStatus.SUCCEEDED,
    intent_id: str = "pi_test",
) -> Payment:
    payment = Payment(
        order_id=order.id,
        provider=provider,
        status=status,
        intent_id=intent_id,
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment


def _link_esim(
    db_session,
    order: Order,
    user: User,
    plan: Plan,
    profile_status: EsimStatus = EsimStatus.ACTIVE,
    inventory_status: EsimInventoryStatus = EsimInventoryStatus.ASSIGNED,
) -> tuple[EsimProfile, EsimInventory]:
    inventory = EsimInventory(
        plan_id=plan.id,
        carrier_id=plan.carrier_id,
        country_id=plan.country_id,
        activation_code="ACT-123",
        iccid="ICCID123",
        status=inventory_status,
    )
    profile = EsimProfile(
        user_id=user.id,
        order_id=order.id,
        plan_id=plan.id,
        country_id=plan.country_id,
        carrier_id=plan.carrier_id,
        inventory_item=inventory,
        status=profile_status,
        activation_code="QR-1",
    )
    db_session.add_all([inventory, profile])
    db_session.commit()
    db_session.refresh(profile)
    db_session.refresh(inventory)
    return profile, inventory


def test_list_orders_filters_and_serializes(client, admin_headers, db_session):
    """Ensure /admin/orders supports filtering and returns nested resources."""
    plan = _create_plan(db_session)
    user_paid = _create_user(db_session, email="paid@example.com")
    user_other = _create_user(db_session, email="other@example.com")

    order_paid = _create_order(db_session, user_paid, plan, OrderStatus.PAID, 2500)
    _add_payment(
        db_session, order_paid, status=PaymentStatus.SUCCEEDED, intent_id="pi_paid"
    )
    _link_esim(db_session, order_paid, user_paid, plan)

    _create_order(db_session, user_other, plan, OrderStatus.CREATED, 5000)

    response = client.get(
        "/admin/orders",
        params={"order_status": "paid", "user_q": "paid@"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    item = payload["items"][0]
    assert item["status"] == "paid"
    assert item["amount_minor_units"] == 2500
    assert item["user"]["email"] == "paid@example.com"
    assert item["payments"][0]["intent_id"] == "pi_paid"
    assert item["esim_profile"]["status"] == "active"


def test_list_payments_filters_by_provider(client, admin_headers, db_session):
    """Payments endpoint should filter by provider and status."""
    plan = _create_plan(db_session, iso2="BR", carrier_name="Carrier BR")
    user = _create_user(db_session, email="pay@example.com")
    order = _create_order(db_session, user, plan, OrderStatus.PAID)
    _add_payment(
        db_session,
        order,
        provider=PaymentProvider.STRIPE,
        status=PaymentStatus.SUCCEEDED,
        intent_id="pi_stripe",
    )
    _add_payment(
        db_session,
        order,
        provider=PaymentProvider.MERCADO_PAGO,
        status=PaymentStatus.FAILED,
        intent_id="pi_mp",
    )

    response = client.get(
        "/admin/payments",
        params={"provider": "stripe", "payment_status": "succeeded"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    payment = data["items"][0]
    assert payment["provider"] == "STRIPE"
    assert payment["status"] == "succeeded"
    assert payment["order_id"] == order.id


def test_list_esims_filters_by_status(client, admin_headers, db_session):
    """eSIM endpoint should filter by profile and inventory statuses."""
    plan = _create_plan(db_session, iso2="CL")
    user = _create_user(db_session, email="esim@example.com")
    order = _create_order(db_session, user, plan)
    _link_esim(
        db_session,
        order,
        user,
        plan,
        profile_status=EsimStatus.ACTIVE,
        inventory_status=EsimInventoryStatus.ASSIGNED,
    )
    _link_esim(
        db_session,
        order,
        user,
        plan,
        profile_status=EsimStatus.RESERVED,
        inventory_status=EsimInventoryStatus.RESERVED,
    )

    response = client.get(
        "/admin/esims",
        params={"esim_status": "active", "inventory_status": "assigned"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    esim = data["items"][0]
    assert esim["status"] == "active"
    assert esim["inventory_item_id"] is not None


def test_list_inventory_supports_search(client, admin_headers, db_session):
    """Inventory listing should support text search and filtering by status."""
    plan = _create_plan(db_session, iso2="UY")
    # Item that should match search
    inv_match = EsimInventory(
        plan_id=plan.id,
        carrier_id=plan.carrier_id,
        country_id=plan.country_id,
        activation_code="MATCH-123",
        iccid="8901MATCH",
        status=EsimInventoryStatus.AVAILABLE,
    )
    # Item that should be filtered out
    inv_other = EsimInventory(
        plan_id=plan.id,
        carrier_id=plan.carrier_id,
        country_id=plan.country_id,
        activation_code="OTHER-999",
        iccid="NOPE",
        status=EsimInventoryStatus.RESERVED,
    )
    db_session.add_all([inv_match, inv_other])
    db_session.commit()

    response = client.get(
        "/admin/inventory",
        params={"q": "MATCH", "inventory_status": "available"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["activation_code"] == "MATCH-123"
    assert item["status"] == "available"


def test_inventory_stats_reports_low_stock(client, admin_headers, db_session):
    """Inventory stats should aggregate totals and produce low stock alerts."""
    plan = _create_plan(db_session, iso2="PE")
    # Two available items (below threshold of 3)
    db_session.add_all(
        [
            EsimInventory(
                plan_id=plan.id,
                carrier_id=plan.carrier_id,
                country_id=plan.country_id,
                status=EsimInventoryStatus.AVAILABLE,
            )
            for _ in range(2)
        ]
    )
    # One reserved item (not counted toward alert, but in totals)
    db_session.add(
        EsimInventory(
            plan_id=plan.id,
            carrier_id=plan.carrier_id,
            country_id=plan.country_id,
            status=EsimInventoryStatus.RESERVED,
        )
    )
    db_session.commit()

    response = client.get(
        "/admin/inventory/stats",
        params={"low_stock_threshold": 3},
        headers=admin_headers,
    )
    assert response.status_code == 200
    stats = response.json()
    assert stats["totals"]["available"] == 2
    assert stats["totals"]["reserved"] == 1
    assert stats["low_stock_alerts"]
    alert = stats["low_stock_alerts"][0]
    assert alert["available"] == 2
    assert alert["plan_id"] == plan.id
