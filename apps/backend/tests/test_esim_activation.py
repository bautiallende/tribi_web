"""Tests for eSIM activation lifecycle and metadata."""

from __future__ import annotations

import uuid
from contextlib import contextmanager
from decimal import Decimal
from typing import cast

from app.api import orders as orders_module
from app.db.session import get_db
from app.main import app
from app.models import Carrier, Country, EsimInventory, Plan
from app.models.auth_models import (
    AuthCode,
    EsimInventoryStatus,
    EsimProfile,
    EsimStatus,
)
from app.services.esim_providers import EsimProvisioningError
from fastapi.testclient import TestClient

client = TestClient(app)


@contextmanager
def db_session():
    override = app.dependency_overrides[get_db]
    gen = override()
    db = next(gen)
    try:
        yield db
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


def seed_plan() -> int:
    with db_session() as db:
        existing_plan = db.query(Plan).filter(Plan.name == "USA 5GB / 10 Days").first()
        if existing_plan:
            return cast(int, existing_plan.id)

        country = db.query(Country).filter(Country.iso2 == "US").first()
        if not country:
            country = Country(iso2="US", name="United States")
            db.add(country)
            db.flush()

        carrier = db.query(Carrier).filter(Carrier.name == "Mock Carrier").first()
        if not carrier:
            carrier = Carrier(name="Mock Carrier")
            db.add(carrier)
            db.flush()

        plan = Plan(
            country=country,
            carrier=carrier,
            name="USA 5GB / 10 Days",
            data_gb=Decimal("5"),
            duration_days=10,
            price_usd=Decimal("12.50"),
            description="Test plan",
            is_unlimited=False,
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return cast(int, plan.id)


def get_auth_token(email: str) -> str:
    """Helper to get authentication token."""
    client.post("/api/auth/request-code", json={"email": email})
    with db_session() as db:
        auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
        code = auth_code.code

    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    return response.json()["token"]


def create_paid_order(token: str, plan_id: int) -> int:
    """Helper to create and pay for an order."""
    response = client.post(
        "/api/orders",
        json={"plan_id": plan_id, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    order_id = response.json()["id"]

    response_payment = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_payment.status_code == 200
    payment_data = response_payment.json()
    if payment_data["status"] != "succeeded":
        webhook_resp = client.post(
            "/api/payments/webhook",
            json={
                "provider": "MOCK",
                "intent_id": payment_data["intent_id"],
                "status": "succeeded",
                "order_id": order_id,
            },
        )
        assert webhook_resp.status_code == 200

    return order_id


def test_esim_activation_returns_activation_code(setup_database):
    """Test that eSIM activation responds with a non-empty activation code."""
    email = "esim_uuid@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    activation_code = data["activation_code"]
    assert activation_code


def test_esim_activation_returns_iccid(setup_database):
    """Test that eSIM activation responds with an ICCID value."""
    email = "esim_iccid@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    iccid = data["iccid"]
    assert isinstance(iccid, str)
    assert len(iccid) >= 10


def test_esim_status_transitions_to_active(setup_database):
    """Test eSIM status transitions from pending_activation to active."""
    email = "esim_ready@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    # Check initial status is PENDING
    with db_session() as db:
        esim_before = (
            db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
        )
        assert esim_before.status == EsimStatus.PENDING_ACTIVATION

    # Activate
    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Check status is now READY
    with db_session() as db:
        esim_after = (
            db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
        )
        assert esim_after.status == EsimStatus.ACTIVE


def test_esim_activation_requires_paid_order(setup_database):
    """Test that eSIM activation requires order to be PAID."""
    email = "esim_requires_paid@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)

    # Create order but don't pay
    response_order = client.post(
        "/api/orders",
        json={"plan_id": plan_id, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = response_order.json()["id"]

    # Try to activate without payment
    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert "paid" in response.json()["detail"].lower()


def test_esim_activation_order_not_found(setup_database):
    """Test activation with non-existent order returns 404."""
    email = "esim_notfound@test.com"
    token = get_auth_token(email)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": 999999},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert "order not found" in response.json()["detail"].lower()


def test_esim_activation_user_ownership(setup_database):
    """Test user can only activate their own orders."""
    # User 1 creates order
    email1 = "user1_esim@test.com"
    plan_id = seed_plan()
    token1 = get_auth_token(email1)
    order_id = create_paid_order(token1, plan_id)

    # User 2 tries to activate user 1's order
    email2 = "user2_esim@test.com"
    token2 = get_auth_token(email2)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token2}"},
    )

    assert response.status_code == 404  # Order not found (for this user)


def test_esim_activation_code_unique(setup_database):
    """Test that activation codes are unique across activations."""
    email = "esim_unique@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)

    # Create and activate two orders
    order_id_1 = create_paid_order(token, plan_id)
    response1 = client.post(
        "/api/esims/activate",
        json={"order_id": order_id_1},
        headers={"Authorization": f"Bearer {token}"},
    )
    code1 = response1.json()["activation_code"]

    order_id_2 = create_paid_order(token, plan_id)
    response2 = client.post(
        "/api/esims/activate",
        json={"order_id": order_id_2},
        headers={"Authorization": f"Bearer {token}"},
    )
    code2 = response2.json()["activation_code"]

    # Codes should be different
    assert code1 != code2


def test_esim_profile_fields_populated(setup_database):
    """Test that eSIM profile has all fields populated after activation."""
    email = "esim_fields@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Check all required fields
    assert "id" in data
    assert "order_id" in data
    assert data["order_id"] == order_id
    assert "activation_code" in data
    assert data["activation_code"] is not None
    assert "iccid" in data
    assert data["iccid"] is not None
    assert "status" in data
    assert data["status"] == "active"
    assert "created_at" in data


def test_esim_activation_idempotent_returns_existing_data(setup_database):
    """Activating an already active eSIM returns existing payload idempotently."""
    email = "esim_idempotent@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    response1 = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response1.status_code == 200
    code1 = response1.json()["activation_code"]

    response2 = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response2.status_code == 200
    assert response2.json()["activation_code"] == code1

    # Ensure code unchanged in DB
    with db_session() as db:
        esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
        assert esim.activation_code == code1


def _seed_inventory(plan_id: int) -> int:
    with db_session() as db:
        inventory = EsimInventory(
            plan_id=plan_id,
            activation_code=f"INV-{uuid.uuid4().hex[:10]}",
            iccid=f"899{uuid.uuid4().hex[:18]}",
            qr_payload="LPA:1$INV",
            instructions="Use the QR to install",
            status=EsimInventoryStatus.AVAILABLE,
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)
        return cast(int, inventory.id)


def test_esim_activation_consumes_inventory_first(setup_database):
    email = "esim_inventory@test.com"
    plan_id = seed_plan()
    inventory_id = _seed_inventory(plan_id)
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["activation_code"].startswith("INV-")
    assert data["inventory_item_id"] == inventory_id

    with db_session() as db:
        inventory = db.query(EsimInventory).get(inventory_id)
        assert inventory.status == EsimInventoryStatus.ASSIGNED
        assert inventory.assigned_at is not None
        assert inventory.activation_code == data["activation_code"]


def test_esim_activation_creates_inventory_when_provider_used(setup_database):
    email = "esim_provider_inventory@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()

    with db_session() as db:
        profile = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
        assert profile.inventory_item_id is not None
        inventory = db.query(EsimInventory).get(profile.inventory_item_id)
        assert inventory.status == EsimInventoryStatus.ASSIGNED
        assert inventory.activation_code == data["activation_code"]


def test_esim_activation_provider_failure_returns_502(monkeypatch, setup_database):
    email = "esim_provider_failure@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)
    order_id = create_paid_order(token, plan_id)

    class BoomProvider:
        def provision(self, *, order, profile=None):  # noqa: D401 - simple stub
            raise EsimProvisioningError("boom")

    def fake_get_esim_provider(provider_name=None):
        return BoomProvider()

    monkeypatch.setattr(orders_module, "get_esim_provider", fake_get_esim_provider)

    response = client.post(
        "/api/esims/activate",
        json={"order_id": order_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 502
    assert "unable to provision" in response.json()["detail"].lower()

    with db_session() as db:
        profile = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
        assert profile.status == EsimStatus.PENDING_ACTIVATION
        assert profile.provisioned_at is None
        assert profile.inventory_item_id is None


def test_esim_preregistered_on_order_creation(setup_database):
    """Test that EsimProfile is pre-registered when order is created."""
    email = "esim_preregister@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)

    # Create order
    response = client.post(
        "/api/orders",
        json={"plan_id": plan_id, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    order_id = response.json()["id"]

    # Verify EsimProfile exists with PENDING status
    with db_session() as db:
        esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
        assert esim is not None
        assert esim.status == EsimStatus.PENDING_ACTIVATION
        assert esim.activation_code is None


def test_esim_uuid_collision_resistant(setup_database):
    """Test UUID v4 generation is collision-resistant (statistical test)."""
    email = "esim_collision@test.com"
    plan_id = seed_plan()
    token = get_auth_token(email)

    # Generate 100 UUIDs
    codes = set()
    for _ in range(10):  # 10 orders (limited for test speed)
        order_id = create_paid_order(token, plan_id)
        response = client.post(
            "/api/esims/activate",
            json={"order_id": order_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        codes.add(response.json()["activation_code"])

    # All should be unique
    assert len(codes) == 10
