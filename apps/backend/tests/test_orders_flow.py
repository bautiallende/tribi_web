from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal
from typing import cast

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import Carrier, Country, Plan
from app.models.auth_models import AuthCode


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
        existing = db.query(Plan).filter(Plan.name == "USA 5GB / 10 Days").first()
        if existing:
            return cast(int, existing.id)

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


def get_auth_token(email: str = "test-orders@tribi.app") -> str:
    response = client.post("/api/auth/request-code", json={"email": email})
    assert response.status_code == 200

    with db_session() as db:
        code = db.query(AuthCode).filter(AuthCode.email == email).first().code

    verify = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert verify.status_code == 200
    return verify.json()["token"]


def test_order_flow_creates_snapshot_and_esim(setup_database):
    plan_id = seed_plan()
    token = get_auth_token()

    order_resp = client.post(
        "/api/orders",
        json={"plan_id": plan_id, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert order_resp.status_code == 200
    order_data = order_resp.json()
    assert order_data["amount_minor_units"] == 1250
    assert order_data["plan_snapshot"]["name"] == "USA 5GB / 10 Days"

    payment_resp = client.post(
        "/api/payments/create",
        json={"order_id": order_data["id"], "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert payment_resp.status_code == 200
    payment_data = payment_resp.json()
    if payment_data["status"] != "succeeded":
        webhook_resp = client.post(
            "/api/payments/webhook",
            json={
                "provider": "MOCK",
                "intent_id": payment_data["intent_id"],
                "status": "succeeded",
                "order_id": order_data["id"],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert webhook_resp.status_code == 200

    orders_before = client.get(
        "/api/orders/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert orders_before.status_code == 200
    mine_before = orders_before.json()
    assert len(mine_before) == 1
    assert mine_before[0]["plan_snapshot"]["name"] == "USA 5GB / 10 Days"
    assert mine_before[0]["esim_profile"]["status"] == "pending_activation"
    assert mine_before[0]["esim_profile"]["activation_code"] is None

    activate_resp = client.post(
        "/api/esims/activate",
        json={"order_id": order_data["id"]},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert activate_resp.status_code == 200
    activation = activate_resp.json()
    assert activation["activation_code"]
    assert activation["status"] == "active"

    list_resp = client.get(
        "/api/esims/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    esims = list_resp.json()
    assert len(esims) == 1
    assert esims[0]["activation_code"] == activation["activation_code"]
    assert esims[0]["plan_snapshot"]["name"] == "USA 5GB / 10 Days"

    orders_after = client.get(
        "/api/orders/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert orders_after.status_code == 200
    mine_after = orders_after.json()
    assert mine_after[0]["esim_profile"]["status"] == "active"
    assert (
        mine_after[0]["esim_profile"]["activation_code"]
        == activation["activation_code"]
    )
