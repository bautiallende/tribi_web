"""Payment provider interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
import uuid


@dataclass
class PaymentIntent:
    """Payment intent response."""

    intent_id: str
    status: str  # requires_action, succeeded, failed
    amount_minor_units: int
    currency: str
    metadata: Optional[Dict[str, Any]] = None


class PaymentProvider(ABC):
    """Abstract payment provider interface."""

    @abstractmethod
    def create_intent(
        self,
        amount_minor_units: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PaymentIntent:
        """Create a payment intent."""
        raise NotImplementedError

    @abstractmethod
    def process_webhook(self, payload: Dict[str, Any]) -> PaymentIntent:
        """Process webhook from payment provider."""
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    """Mock payment provider for development and testing."""

    def create_intent(
        self,
        amount_minor_units: int,
        currency: str,
        metadata: Optional[Dict[str, Any]] = None,
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
        intent_id = payload.get("intent_id") or f"mock_intent_{uuid.uuid4().hex[:16]}"
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


def get_payment_provider(provider_name: str = "MOCK") -> PaymentProvider:
    """Factory function to get payment provider instance."""
    providers = {
        "MOCK": MockPaymentProvider,
        # Add other providers here: "STRIPE": StripePaymentProvider, etc.
    }

    provider_class = providers.get(provider_name.upper())
    if not provider_class:
        raise ValueError(f"Unknown payment provider: {provider_name}")

    return provider_class()
