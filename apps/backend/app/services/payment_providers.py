"""Payment provider interfaces and implementations."""

from __future__ import annotations

import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, cast

from ..core.config import settings

try:  # pragma: no cover - import guarded for optional dependency in tests
    import stripe as stripe_module
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    stripe_module = None

stripe = cast(Any, stripe_module)

logger = logging.getLogger(__name__)


@dataclass
class PaymentIntent:
    """Payment intent response."""

    intent_id: str
    status: str  # requires_action, succeeded, failed
    amount_minor_units: int
    currency: str
    client_secret: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentWebhookValidationError(Exception):
    """Raised when a webhook payload cannot be validated."""


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    def create_intent(
        self,
        amount_minor_units: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> PaymentIntent:
        """Create a payment intent."""
        raise NotImplementedError

    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> PaymentIntent:
        """Process webhook from payment provider."""
        raise NotImplementedError

    def parse_webhook_payload(
        self, body: bytes, headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Default webhook payload parser (JSON)."""
        del headers
        if not body:
            return {}
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise PaymentWebhookValidationError("Invalid JSON payload") from exc


class MockPaymentProvider(PaymentProvider):
    """Mock payment provider for development and testing."""

    def create_intent(
        self,
        amount_minor_units: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> PaymentIntent:
        """Create a mock payment intent that initially requires customer action."""
        intent_id = f"mock_intent_{uuid.uuid4().hex[:16]}"
        return PaymentIntent(
            intent_id=intent_id,
            status="requires_action",
            amount_minor_units=amount_minor_units,
            currency=currency,
            metadata=metadata or {},
        )

    def process_webhook(self, payload: Dict[str, Any]) -> PaymentIntent:
        """Process mock webhook - always succeeds or fails based on payload."""
        intent_id = payload.get("intent_id") or ""
        status = payload.get("status")
        if not status:
            action = payload.get("action", "succeed")  # legacy field
            status = "succeeded" if action == "succeed" else "failed"

        amount_minor_units = payload.get(
            "amount_minor_units",
            payload.get("amount", 0),
        )

        return PaymentIntent(
            intent_id=intent_id,
            status=status,
            amount_minor_units=amount_minor_units,
            currency=payload.get("currency", "USD"),
            metadata=payload.get("metadata", {}),
        )


class StripePaymentProvider(PaymentProvider):
    """Stripe payment provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        if stripe is None:  # pragma: no cover - ensured via dependency
            raise ImportError("stripe package is required for Stripe provider")

        self.api_key = api_key or settings.STRIPE_SECRET_KEY
        self.webhook_secret = webhook_secret or settings.STRIPE_WEBHOOK_SECRET

        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY is not configured")

        stripe.api_key = self.api_key

    def create_intent(
        self,
        amount_minor_units: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
    ) -> PaymentIntent:
        if amount_minor_units <= 0:
            raise ValueError("Amount must be greater than zero")

        payload: Dict[str, Any] = {
            "amount": amount_minor_units,
            "currency": currency.lower(),
            "metadata": metadata or {},
            "automatic_payment_methods": {
                "enabled": settings.STRIPE_AUTO_PAYMENT_METHODS
            },
        }

        if settings.STRIPE_PAYMENT_METHOD_TYPES:
            payload["payment_method_types"] = settings.STRIPE_PAYMENT_METHOD_TYPES

        if idempotency_key:
            payload["idempotency_key"] = idempotency_key

        intent = stripe.PaymentIntent.create(**payload)
        normalized_status = self._normalize_status(intent.get("status", ""))
        client_secret = intent.get("client_secret")

        return PaymentIntent(
            intent_id=intent["id"],
            status=normalized_status,
            amount_minor_units=int(intent["amount"]),
            currency=str(intent["currency"]).upper(),
            client_secret=client_secret,
            metadata=intent.get("metadata"),
        )

    def process_webhook(self, payload: Dict[str, Any]) -> PaymentIntent:
        event_type = payload.get("type")
        data_object = payload.get("data", {}).get("object", {})

        if not data_object:
            raise PaymentWebhookValidationError(
                "Missing payment object in webhook payload"
            )

        status = self._status_from_event(event_type, data_object.get("status"))

        return PaymentIntent(
            intent_id=data_object.get("id", ""),
            status=status,
            amount_minor_units=int(data_object.get("amount", 0)),
            currency=str(
                data_object.get("currency", settings.DEFAULT_CURRENCY)
            ).upper(),
            client_secret=data_object.get("client_secret"),
            metadata=data_object.get("metadata"),
        )

    def parse_webhook_payload(
        self, body: bytes, headers: Dict[str, str]
    ) -> Dict[str, Any]:
        if not self.webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET is not configured")

        signature_header = (
            headers.get("stripe-signature")
            or headers.get("Stripe-Signature")
            or headers.get("STRIPE-SIGNATURE")
        )
        if not signature_header:
            raise PaymentWebhookValidationError("Missing Stripe-Signature header")

        try:
            event = stripe.Webhook.construct_event(
                payload=body,
                sig_header=signature_header,
                secret=self.webhook_secret,
            )
        except stripe.error.SignatureVerificationError as exc:  # type: ignore[attr-defined]
            logger.warning("Stripe webhook signature verification failed: %s", exc)
            raise PaymentWebhookValidationError(
                "Invalid Stripe webhook signature"
            ) from exc

        return event

    @staticmethod
    def _normalize_status(status: str | None) -> str:
        normalized = (status or "requires_action").lower()
        if normalized == "succeeded":
            return "succeeded"
        if normalized in {"canceled"}:
            return "failed"
        return "requires_action"

    @staticmethod
    def _status_from_event(event_type: str | None, status: str | None) -> str:
        if event_type == "payment_intent.succeeded":
            return "succeeded"
        if event_type in {"payment_intent.payment_failed", "payment_intent.canceled"}:
            return "failed"
        return StripePaymentProvider._normalize_status(status)


def get_payment_provider(provider_name: str | None = None) -> PaymentProvider:
    """Factory function to get payment provider instance."""
    normalized_name = (provider_name or settings.PAYMENT_PROVIDER or "MOCK").upper()

    if normalized_name == "STRIPE":
        return StripePaymentProvider()

    providers = {
        "MOCK": MockPaymentProvider,
    }

    provider_class = providers.get(normalized_name)
    if not provider_class:
        raise ValueError(f"Unknown payment provider: {normalized_name}")

    return provider_class()
