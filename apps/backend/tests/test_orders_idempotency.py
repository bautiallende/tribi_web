"""Tests for order idempotency."""

from typing import cast

from app.main import app
from app.models.auth_models import AuthCode, EsimStatus, Order
from fastapi.testclient import TestClient

from .conftest import TestingSessionLocal

client = TestClient(app)


def _get_code(email: str) -> str:
    db = TestingSessionLocal()
    try:
        auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
        assert auth_code is not None
        return str(auth_code.code)
    finally:
        db.close()


def get_auth_token(email: str) -> str:
    """Helper to get authentication token."""
    client.post("/api/auth/request-code", json={"email": email})
    code = _get_code(email)

    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    return response.json()["token"]


def test_idempotent_order_creation():
    """Test that same idempotency key returns same order."""
    email = "idempotent@test.com"
    token = get_auth_token(email)
    idempotency_key = "test-key-12345"

    # First request
    response1 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response1.status_code == 200
    order1 = response1.json()
    order_id_1 = order1["id"]

    # Second request with same key
    response2 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response2.status_code == 200
    order2 = response2.json()
    order_id_2 = order2["id"]

    # Should return same order
    assert order_id_1 == order_id_2


def test_different_idempotency_keys_create_different_orders():
    """Test that different idempotency keys create different orders."""
    email = "different_keys@test.com"
    token = get_auth_token(email)

    # First request
    response1 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-1"},
    )
    assert response1.status_code == 200
    order_id_1 = response1.json()["id"]

    # Second request with different key
    response2 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "key-2"},
    )
    assert response2.status_code == 200
    order_id_2 = response2.json()["id"]

    # Should create different orders
    assert order_id_1 != order_id_2


def test_no_idempotency_key_creates_new_orders():
    """Test that requests without idempotency key create new orders each time."""
    email = "no_key@test.com"
    token = get_auth_token(email)

    # First request without key
    response1 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response1.status_code == 200
    order_id_1 = response1.json()["id"]

    # Second request without key
    response2 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response2.status_code == 200
    order_id_2 = response2.json()["id"]

    # Should create different orders
    assert order_id_1 != order_id_2


def test_idempotency_key_stored_in_database():
    """Test that idempotency key is stored in Order model."""
    email = "key_stored@test.com"
    token = get_auth_token(email)
    idempotency_key = "stored-key-67890"

    response = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response.status_code == 200
    order_id = response.json()["id"]

    # Verify key is stored in database
    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    assert order is not None
    order = cast(Order, order)
    idempotency_value = getattr(order, "idempotency_key")
    assert idempotency_value is not None
    stored_key = str(idempotency_value)
    assert stored_key.endswith(idempotency_key)
    assert stored_key.startswith(f"{order.user_id}:")
    db.close()


def test_idempotency_with_different_plan_id():
    """Test idempotency returns same order even if plan_id differs in retry."""
    email = "different_plan@test.com"
    token = get_auth_token(email)
    idempotency_key = "same-key-different-plan"

    # First request with plan_id=1
    response1 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response1.status_code == 200
    order1 = response1.json()

    # Second request with plan_id=2 but same key
    response2 = client.post(
        "/api/orders",
        json={"plan_id": 2, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response2.status_code == 200
    order2 = response2.json()

    # Should return same order (idempotency key wins)
    assert order1["id"] == order2["id"]
    assert order1["plan_id"] == order2["plan_id"]  # Original plan_id preserved


def test_esim_profile_created_with_order():
    """Test that EsimProfile is pre-registered when order is created."""
    from app.models.auth_models import EsimProfile

    email = "esim_preregister@test.com"
    token = get_auth_token(email)

    response = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    order_id = response.json()["id"]

    # Verify EsimProfile was created
    db = TestingSessionLocal()
    esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
    assert esim is not None
    assert cast(EsimStatus, esim.status) == EsimStatus.PENDING_ACTIVATION
    db.close()


def test_idempotency_atomic_transaction():
    """Test that Order + EsimProfile creation is atomic."""
    from app.models.auth_models import EsimProfile

    email = "atomic@test.com"
    token = get_auth_token(email)
    idempotency_key = "atomic-key-123"

    # Create order
    response = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response.status_code == 200
    order_id = response.json()["id"]

    # Verify both Order and EsimProfile exist
    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()

    assert order is not None
    assert esim is not None
    order = cast(Order, order)
    assert getattr(esim, "order_id") == getattr(order, "id")
    db.close()


def test_idempotency_key_unique_constraint():
    """Test that idempotency_key has unique constraint (database level)."""
    email = "unique_constraint@test.com"
    token = get_auth_token(email)
    idempotency_key = "unique-key-999"

    # First request
    response1 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response1.status_code == 200
    order_id = response1.json()["id"]

    # Try to manually create another order with same key (should fail at DB level)
    db = TestingSessionLocal()
    try:
        existing = db.query(Order).filter(Order.id == order_id).first()
        assert existing is not None
        stored_key = getattr(existing, "idempotency_key")
        assert stored_key is not None
        duplicate_order = Order(
            user_id=1,
            plan_id=2,
            idempotency_key=stored_key,
            status="CREATED",
            currency="EUR",
            amount_minor_units=5000,
        )
        db.add(duplicate_order)
        db.commit()
        assert False, "Should have raised IntegrityError"
    except Exception as e:
        # SQLite: UNIQUE constraint failed
        # MySQL: Duplicate entry
        assert "unique" in str(e).lower() or "duplicate" in str(e).lower()
    finally:
        db.rollback()
        db.close()


def test_idempotency_different_users_same_key():
    """Test that different users can use the same idempotency key."""
    idempotency_key = "shared-key-456"

    # User 1
    email1 = "user1_samekey@test.com"
    token1 = get_auth_token(email1)
    response1 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token1}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response1.status_code == 200
    order_id_1 = response1.json()["id"]

    # User 2 with same key
    email2 = "user2_samekey@test.com"
    token2 = get_auth_token(email2)
    response2 = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={
            "Authorization": f"Bearer {token2}",
            "Idempotency-Key": idempotency_key,
        },
    )
    assert response2.status_code == 200
    order_id_2 = response2.json()["id"]

    # Should create different orders (different users)
    assert order_id_1 != order_id_2
