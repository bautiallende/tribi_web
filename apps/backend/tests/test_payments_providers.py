"""Tests for payment provider system."""

from typing import cast

from app.main import app
from app.models.auth_models import AuthCode, Order, Payment, PaymentStatus
from app.services.payment_providers import MockPaymentProvider, get_payment_provider
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


def create_order(token: str) -> int:
    """Helper to create an order."""
    response = client.post(
        "/api/orders",
        json={"plan_id": 1, "currency": "USD"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()
    return response.json()["id"]


def test_mock_provider_create_intent():
    """Test MockPaymentProvider.create_intent() returns requires_action."""
    provider = MockPaymentProvider()

    intent = provider.create_intent(
        amount_minor_units=9900, currency="USD", metadata={"order_id": 123}
    )

    assert intent.status == "requires_action"
    assert intent.amount_minor_units == 9900
    assert intent.currency == "USD"
    assert "mock_" in intent.intent_id
    assert intent.metadata is not None
    assert intent.metadata["order_id"] == 123


def test_mock_provider_webhook_success():
    """Test MockPaymentProvider.process_webhook() with succeeded status."""
    provider = MockPaymentProvider()

    intent = provider.process_webhook(
        {
            "intent_id": "mock_12345",
            "status": "succeeded",
            "amount": 9900,
            "currency": "USD",
        }
    )

    assert intent.status == "succeeded"
    assert intent.intent_id == "mock_12345"


def test_mock_provider_webhook_failed():
    """Test MockPaymentProvider.process_webhook() with failed status."""
    provider = MockPaymentProvider()

    intent = provider.process_webhook(
        {
            "intent_id": "mock_67890",
            "status": "failed",
            "amount": 9900,
            "currency": "USD",
        }
    )

    assert intent.status == "failed"


def test_get_payment_provider_mock():
    """Test get_payment_provider factory returns MockProvider."""
    provider = get_payment_provider("MOCK")
    assert isinstance(provider, MockPaymentProvider)


def test_get_payment_provider_case_insensitive():
    """Test get_payment_provider is case-insensitive."""
    provider1 = get_payment_provider("mock")
    provider2 = get_payment_provider("MOCK")
    provider3 = get_payment_provider("Mock")

    assert isinstance(provider1, MockPaymentProvider)
    assert isinstance(provider2, MockPaymentProvider)
    assert isinstance(provider3, MockPaymentProvider)


def test_create_payment_intent():
    """Test POST /payments/create creates payment intent."""
    email = "payment_create@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    response = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "requires_action"
    assert "intent_id" in data
    assert "mock_" in data["intent_id"]
    assert data["provider"] == "MOCK"
    assert data["amount_minor_units"] == 9900
    assert data["currency"] == "USD"


def test_payment_record_created():
    """Test that Payment record is created in database."""
    email = "payment_record@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    response = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )

    intent_id = response.json()["intent_id"]

    # Verify Payment record
    db = TestingSessionLocal()
    payment = db.query(Payment).filter(Payment.intent_id == intent_id).first()
    assert payment is not None
    payment = cast(Payment, payment)
    assert getattr(payment, "order_id") == order_id
    assert str(payment.provider) == "PaymentProvider.MOCK"
    assert str(payment.status) == "PaymentStatus.REQUIRES_ACTION"
    db.close()


def test_webhook_payment_succeeded():
    """Test webhook with succeeded updates order to PAID."""
    email = "webhook_success@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    # Create payment
    response_create = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    intent_id = response_create.json()["intent_id"]

    # Send webhook
    response_webhook = client.post(
        "/api/payments/webhook",
        json={"provider": "MOCK", "intent_id": intent_id, "status": "succeeded"},
    )

    assert response_webhook.status_code == 200
    data = response_webhook.json()
    assert data["status"] == "processed"
    assert data["intent_status"] == "succeeded"

    # Verify order status updated
    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    assert order is not None
    order = cast(Order, order)
    assert str(order.status) == "OrderStatus.PAID"
    db.close()


def test_webhook_payment_failed():
    """Test webhook with failed updates order to FAILED."""
    email = "webhook_failed@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    # Create payment
    response_create = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    intent_id = response_create.json()["intent_id"]

    # Send webhook with failed status
    response_webhook = client.post(
        "/api/payments/webhook",
        json={"provider": "MOCK", "intent_id": intent_id, "status": "failed"},
    )

    assert response_webhook.status_code == 200

    # Verify order status updated to FAILED
    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    assert order is not None
    order = cast(Order, order)
    assert str(order.status) == "OrderStatus.FAILED"
    db.close()


def test_webhook_updates_payment_status():
    """Test webhook updates Payment.status."""
    email = "webhook_payment_status@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    # Create payment
    response_create = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    intent_id = response_create.json()["intent_id"]

    # Send webhook
    client.post(
        "/api/payments/webhook",
        json={"provider": "MOCK", "intent_id": intent_id, "status": "succeeded"},
    )

    # Verify Payment.status updated
    db = TestingSessionLocal()
    payment = db.query(Payment).filter(Payment.intent_id == intent_id).first()
    assert payment is not None
    payment = cast(Payment, payment)
    assert str(payment.status) == "PaymentStatus.SUCCEEDED"
    db.close()


def test_webhook_missing_intent_id():
    """Test webhook without intent_id returns 400."""
    response = client.post(
        "/api/payments/webhook", json={"provider": "MOCK", "status": "succeeded"}
    )
    assert response.status_code == 400
    assert "missing intent_id" in response.json()["detail"].lower()


def test_webhook_intent_not_found():
    """Test webhook with unknown intent_id returns 404."""
    response = client.post(
        "/api/payments/webhook",
        json={
            "provider": "MOCK",
            "intent_id": "nonexistent_intent",
            "status": "succeeded",
        },
    )
    assert response.status_code == 404
    assert "payment not found" in response.json()["detail"].lower()


def test_payment_intent_id_unique():
    """Test that intent_id is unique in database."""
    email = "intent_unique@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    # Create payment
    response = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    intent_id = response.json()["intent_id"]

    # Try to create another payment with same intent_id (should fail)
    db = TestingSessionLocal()
    try:
        duplicate_payment = Payment(
            order_id=order_id,
            provider="MOCK",
            status=PaymentStatus.REQUIRES_ACTION,
            intent_id=intent_id,
            raw_payload={},
        )
        db.add(duplicate_payment)
        db.commit()
        assert False, "Should have raised IntegrityError"
    except Exception as e:
        assert "unique" in str(e).lower() or "duplicate" in str(e).lower()
    finally:
        db.rollback()
        db.close()


def test_order_status_flow():
    """Test complete order status flow: CREATED -> PAID."""
    email = "status_flow@test.com"
    token = get_auth_token(email)

    # Create order (should be CREATED)
    order_id = create_order(token)
    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    assert order is not None
    order = cast(Order, order)
    assert str(order.status) == "OrderStatus.CREATED"
    db.close()

    # Create payment (order still CREATED)
    response_payment = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    intent_id = response_payment.json()["intent_id"]

    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    assert order is not None
    order = cast(Order, order)
    assert str(order.status) == "OrderStatus.CREATED"
    db.close()

    # Webhook succeeds (order -> PAID)
    client.post(
        "/api/payments/webhook",
        json={"provider": "MOCK", "intent_id": intent_id, "status": "succeeded"},
    )

    db = TestingSessionLocal()
    order = db.query(Order).filter(Order.id == order_id).first()
    assert order is not None
    order = cast(Order, order)
    assert str(order.status) == "OrderStatus.PAID"
    db.close()


def test_payment_status_flow():
    """Test complete payment status flow: REQUIRES_ACTION -> SUCCEEDED."""
    email = "payment_flow@test.com"
    token = get_auth_token(email)
    order_id = create_order(token)

    # Create payment (REQUIRES_ACTION)
    response_payment = client.post(
        "/api/payments/create",
        json={"order_id": order_id, "provider": "MOCK"},
        headers={"Authorization": f"Bearer {token}"},
    )
    intent_id = response_payment.json()["intent_id"]

    db = TestingSessionLocal()
    payment = db.query(Payment).filter(Payment.intent_id == intent_id).first()
    assert payment is not None
    payment = cast(Payment, payment)
    assert str(payment.status) == "PaymentStatus.REQUIRES_ACTION"
    db.close()

    # Webhook (SUCCEEDED)
    client.post(
        "/api/payments/webhook",
        json={"provider": "MOCK", "intent_id": intent_id, "status": "succeeded"},
    )

    db = TestingSessionLocal()
    payment = db.query(Payment).filter(Payment.intent_id == intent_id).first()
    assert payment is not None
    payment = cast(Payment, payment)
    assert str(payment.status) == "PaymentStatus.SUCCEEDED"
    db.close()
