"""Tests for eSIM activation with UUID."""
import re
from fastapi.testclient import TestClient

from app.main import app
from app.models.auth_models import AuthCode, EsimProfile, EsimStatus
from .conftest import TestingSessionLocal


client = TestClient(app)


def get_auth_token(email: str) -> str:
    """Helper to get authentication token."""
    client.post("/auth/request-code", json={"email": email})
    db = TestingSessionLocal()
    auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
    code = auth_code.code
    db.close()
    
    response = client.post("/auth/verify-code", json={"email": email, "code": code})
    return response.json()["access_token"]


def create_paid_order(token: str) -> int:
    """Helper to create and pay for an order."""
    # Create order
    response = client.post(
        "/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"}
    )
    order_id = response.json()["id"]
    
    # Create payment
    response_payment = client.post(
        "/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"}
    )
    intent_id = response_payment.json()["intent_id"]
    
    # Webhook to mark as paid
    client.post(
        "/payments/webhook",
        json={"provider": "MOCK", "intent_id": intent_id, "status": "succeeded"}
    )
    
    return order_id


def test_esim_activation_generates_uuid():
    """Test that eSIM activation generates UUID v4 activation code."""
    email = "esim_uuid@test.com"
    token = get_auth_token(email)
    order_id = create_paid_order(token)
    
    response = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check activation_code is UUID v4 format
    activation_code = data["activation_code"]
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    assert re.match(uuid_pattern, activation_code, re.IGNORECASE), f"Not a valid UUID v4: {activation_code}"


def test_esim_activation_generates_iccid():
    """Test that eSIM activation generates ICCID."""
    email = "esim_iccid@test.com"
    token = get_auth_token(email)
    order_id = create_paid_order(token)
    
    response = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check ICCID format
    iccid = data["iccid"]
    assert iccid.startswith("89001")
    assert len(iccid) == 22  # 89001 + 17 hex digits


def test_esim_status_transitions_to_ready():
    """Test eSIM status transitions from PENDING to READY."""
    email = "esim_ready@test.com"
    token = get_auth_token(email)
    order_id = create_paid_order(token)
    
    # Check initial status is PENDING
    db = TestingSessionLocal()
    esim_before = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
    assert str(esim_before.status) == "EsimStatus.PENDING"
    db.close()
    
    # Activate
    response = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    # Check status is now READY
    db = TestingSessionLocal()
    esim_after = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
    assert str(esim_after.status) == "EsimStatus.READY"
    db.close()


def test_esim_activation_requires_paid_order():
    """Test that eSIM activation requires order to be PAID."""
    email = "esim_requires_paid@test.com"
    token = get_auth_token(email)
    
    # Create order but don't pay
    response_order = client.post(
        "/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"}
    )
    order_id = response_order.json()["id"]
    
    # Try to activate without payment
    response = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 400
    assert "paid" in response.json()["detail"].lower()


def test_esim_activation_order_not_found():
    """Test activation with non-existent order returns 404."""
    email = "esim_notfound@test.com"
    token = get_auth_token(email)
    
    response = client.post(
        f"/esims/activate?order_id=999999",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "order not found" in response.json()["detail"].lower()


def test_esim_activation_user_ownership():
    """Test user can only activate their own orders."""
    # User 1 creates order
    email1 = "user1_esim@test.com"
    token1 = get_auth_token(email1)
    order_id = create_paid_order(token1)
    
    # User 2 tries to activate user 1's order
    email2 = "user2_esim@test.com"
    token2 = get_auth_token(email2)
    
    response = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token2}"}
    )
    
    assert response.status_code == 404  # Order not found (for this user)


def test_esim_activation_code_unique():
    """Test that activation codes are unique across activations."""
    email = "esim_unique@test.com"
    token = get_auth_token(email)
    
    # Create and activate two orders
    order_id_1 = create_paid_order(token)
    response1 = client.post(
        f"/esims/activate?order_id={order_id_1}",
        headers={"Authorization": f"Bearer {token}"}
    )
    code1 = response1.json()["activation_code"]
    
    order_id_2 = create_paid_order(token)
    response2 = client.post(
        f"/esims/activate?order_id={order_id_2}",
        headers={"Authorization": f"Bearer {token}"}
    )
    code2 = response2.json()["activation_code"]
    
    # Codes should be different
    assert code1 != code2


def test_esim_profile_fields_populated():
    """Test that eSIM profile has all fields populated after activation."""
    email = "esim_fields@test.com"
    token = get_auth_token(email)
    order_id = create_paid_order(token)
    
    response = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
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
    assert data["status"] == "READY"
    assert "created_at" in data


def test_esim_activation_idempotent():
    """Test that activating same order twice returns same eSIM."""
    email = "esim_idempotent@test.com"
    token = get_auth_token(email)
    order_id = create_paid_order(token)
    
    # First activation
    response1 = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response1.status_code == 200
    code1 = response1.json()["activation_code"]
    
    # Second activation (should return same eSIM)
    response2 = client.post(
        f"/esims/activate?order_id={order_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response2.status_code == 200
    code2 = response2.json()["activation_code"]
    
    # Should return same activation code
    assert code1 == code2


def test_esim_preregistered_on_order_creation():
    """Test that EsimProfile is pre-registered when order is created."""
    email = "esim_preregister@test.com"
    token = get_auth_token(email)
    
    # Create order
    response = client.post(
        "/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"}
    )
    order_id = response.json()["id"]
    
    # Verify EsimProfile exists with PENDING status
    db = TestingSessionLocal()
    esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
    assert esim is not None
    assert str(esim.status) == "EsimStatus.PENDING"
    assert esim.activation_code is None  # Not yet activated
    db.close()


def test_esim_uuid_collision_resistant():
    """Test UUID v4 generation is collision-resistant (statistical test)."""
    email = "esim_collision@test.com"
    token = get_auth_token(email)
    
    # Generate 100 UUIDs
    codes = set()
    for _ in range(10):  # 10 orders (limited for test speed)
        order_id = create_paid_order(token)
        response = client.post(
            f"/esims/activate?order_id={order_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        codes.add(response.json()["activation_code"])
    
    # All should be unique
    assert len(codes) == 10
