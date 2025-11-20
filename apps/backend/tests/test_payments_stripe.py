import pytest
from app.services.payment_providers import (
    PaymentWebhookValidationError,
    StripePaymentProvider,
)


@pytest.fixture
def stripe_provider():
    return StripePaymentProvider(api_key="sk_test_123", webhook_secret="whsec_123")


def test_stripe_provider_creates_intent(monkeypatch, stripe_provider):
    created_payload = {}

    def fake_create(**kwargs):
        created_payload.update(kwargs)
        return {
            "id": "pi_123",
            "status": "requires_payment_method",
            "amount": kwargs["amount"],
            "currency": kwargs["currency"],
            "client_secret": "cs_test_123",
            "metadata": kwargs["metadata"],
        }

    monkeypatch.setattr("stripe.PaymentIntent.create", fake_create)

    intent = stripe_provider.create_intent(
        amount_minor_units=5000,
        currency="USD",
        metadata={"order_id": 1},
        idempotency_key="user-1:order-1",
    )

    assert created_payload["amount"] == 5000
    assert created_payload["currency"] == "usd"
    assert created_payload["idempotency_key"] == "user-1:order-1"
    assert intent.intent_id == "pi_123"
    assert intent.status == "requires_action"
    assert intent.client_secret == "cs_test_123"


def test_stripe_provider_processes_success_event(stripe_provider):
    event = {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_456",
                "amount": 1000,
                "currency": "usd",
                "metadata": {"order_id": 99},
            }
        },
    }

    intent = stripe_provider.process_webhook(event)

    assert intent.intent_id == "pi_456"
    assert intent.status == "succeeded"
    assert intent.amount_minor_units == 1000
    assert intent.currency == "USD"
    assert intent.metadata == {"order_id": 99}


def test_stripe_provider_webhook_validation(monkeypatch, stripe_provider):
    dummy_event = {
        "type": "payment_intent.payment_failed",
        "data": {"object": {"id": "pi_789", "amount": 500, "currency": "usd"}},
    }

    def fake_construct_event(payload, sig_header, secret):
        assert payload == b"{}"
        assert sig_header == "sig_test"
        assert secret == "whsec_123"
        return dummy_event

    monkeypatch.setattr("stripe.Webhook.construct_event", fake_construct_event)

    parsed = stripe_provider.parse_webhook_payload(
        b"{}", {"stripe-signature": "sig_test"}
    )
    assert parsed == dummy_event


def test_stripe_provider_webhook_validation_failure(stripe_provider):
    with pytest.raises(PaymentWebhookValidationError):
        stripe_provider.parse_webhook_payload(b"{}", {})
