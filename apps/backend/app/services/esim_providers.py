"""eSIM provisioning providers and ConnectedYou scaffolding."""

from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Optional

import httpx

from ..core.config import settings

if TYPE_CHECKING:  # pragma: no cover - imports for type checking only
    from ..models import EsimProfile, Order

logger = logging.getLogger(__name__)


@dataclass
class EsimProvisioningResult:
    """Normalized data returned by any eSIM provider."""

    activation_code: str
    iccid: Optional[str] = None
    qr_payload: Optional[str] = None
    instructions: Optional[str] = None
    provider_reference: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EsimProvisioningError(Exception):
    """Raised when provisioning cannot be completed."""


class EsimProvider(ABC):
    """Interface for classes that can provision eSIMs."""

    @abstractmethod
    def provision(
        self, *, order: "Order", profile: "EsimProfile" | None = None
    ) -> EsimProvisioningResult:
        """Provision or assign an eSIM for the given order/profile."""
        raise NotImplementedError


class LocalEsimProvider(EsimProvider):
    """Development/default provider that mimics provisioning locally."""

    def provision(
        self, *, order: "Order", profile: "EsimProfile" | None = None
    ) -> EsimProvisioningResult:
        del order  # Only used for parity with interface
        activation_code = (
            profile.activation_code
            if profile and profile.activation_code
            else f"LOCAL-{uuid.uuid4().hex[:16]}"
        )
        iccid = (
            profile.iccid if profile and profile.iccid else f"89{uuid.uuid4().hex[:18]}"
        )
        qr_payload = profile.qr_payload or f"LPA:1${activation_code}"
        instructions = profile.instructions or (
            "Install via Settings > Cellular > Add eSIM and scan the QR or enter the activation code manually."
        )

        return EsimProvisioningResult(
            activation_code=activation_code,
            iccid=iccid,
            qr_payload=qr_payload,
            instructions=instructions,
            metadata={"provider": "LOCAL"},
        )


class ConnectedYouProvider(EsimProvider):
    """ConnectedYou integration scaffolding.

    The provider operates in dry-run mode by default so we can build requests,
    store metadata, and flip the switch once credentials + approval are ready.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        partner_id: str | None = None,
        timeout_seconds: int | None = None,
        dry_run: bool | None = None,
    ) -> None:
        self.base_url = (base_url or settings.CONNECTED_YOU_BASE_URL or "").rstrip("/")
        self.api_key = api_key or settings.CONNECTED_YOU_API_KEY
        self.partner_id = partner_id or settings.CONNECTED_YOU_PARTNER_ID
        self.timeout = timeout_seconds or settings.CONNECTED_YOU_TIMEOUT_SECONDS
        self.dry_run = settings.CONNECTED_YOU_DRY_RUN if dry_run is None else dry_run

        if not self.partner_id:
            raise EsimProvisioningError("CONNECTED_YOU_PARTNER_ID is not configured")
        if not self.api_key and not self.dry_run:
            raise EsimProvisioningError("CONNECTED_YOU_API_KEY is not configured")

    def provision(
        self, *, order: "Order", profile: "EsimProfile" | None = None
    ) -> EsimProvisioningResult:
        payload = self._build_payload(order=order, profile=profile)

        if self.dry_run:
            logger.info(
                "ConnectedYou dry-run payload for order %s: %s", order.id, payload
            )
            return self._fake_result(payload)

        response_data = self._post("/partners/orders", payload)
        return self._parse_response(response_data)

    def _build_payload(
        self, *, order: "Order", profile: "EsimProfile" | None = None
    ) -> Dict[str, Any]:
        plan_snapshot = getattr(order, "plan_snapshot", None) or {}
        user = getattr(order, "user", None) or getattr(profile, "user", None)
        customer_payload: Dict[str, Any] = {}
        if user and getattr(user, "email", None):
            customer_payload["email"] = user.email
        if user and getattr(user, "name", None):
            customer_payload["name"] = user.name

        country_iso2 = plan_snapshot.get("country_iso2")
        if not country_iso2 and profile and getattr(profile, "country", None):
            country_iso2 = getattr(profile.country, "iso2", None)

        return {
            "partnerId": self.partner_id,
            "orderReference": f"order-{order.id}",
            "planCode": plan_snapshot.get("external_id")
            or plan_snapshot.get("id")
            or order.plan_id,
            "countryIso2": country_iso2,
            "carrierName": plan_snapshot.get("carrier_name"),
            "quantity": 1,
            "customer": customer_payload,
            "metadata": {
                "plan_name": plan_snapshot.get("name"),
                "order_id": order.id,
            },
            "simProfile": {
                "activationCode": getattr(profile, "activation_code", None),
                "iccid": getattr(profile, "iccid", None),
            },
        }

    def _fake_result(self, payload: Dict[str, Any]) -> EsimProvisioningResult:
        activation_code = f"CNY-{uuid.uuid4().hex[:12]}".upper()
        iccid = f"882{uuid.uuid4().hex[:17]}"
        qr_payload = f"LPA:1${activation_code}"
        metadata = {"provider": "CONNECTED_YOU", "dry_run_payload": payload}

        return EsimProvisioningResult(
            activation_code=activation_code,
            iccid=iccid,
            qr_payload=qr_payload,
            instructions=(
                "ConnectedYou provisioning (dry run). Install the profile using standard device instructions."
            ),
            provider_reference=payload.get("orderReference"),
            metadata=metadata,
        )

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.base_url:
            raise EsimProvisioningError("CONNECTED_YOU_BASE_URL is not configured")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        try:
            response = httpx.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except httpx.HTTPError as exc:  # pragma: no cover - network failure
            logger.error("ConnectedYou request failed: %s", exc)
            raise EsimProvisioningError(f"ConnectedYou request failed: {exc}") from exc

        return response.json()

    def _parse_response(self, data: Dict[str, Any]) -> EsimProvisioningResult:
        profile_data = data.get("data") or data
        activation_code = profile_data.get("activationCode") or profile_data.get(
            "activation_code"
        )
        if not activation_code:
            raise EsimProvisioningError("ConnectedYou response missing activation code")

        return EsimProvisioningResult(
            activation_code=activation_code,
            iccid=profile_data.get("iccid"),
            qr_payload=profile_data.get("qrCode") or profile_data.get("qr_payload"),
            instructions=profile_data.get("instructions"),
            provider_reference=profile_data.get("orderReference")
            or profile_data.get("id"),
            metadata={"provider": "CONNECTED_YOU", "raw": data},
        )


def get_esim_provider(provider_name: str | None = None) -> EsimProvider:
    """Return the configured eSIM provider implementation."""

    normalized = (provider_name or settings.ESIM_PROVIDER or "LOCAL").upper()
    if normalized == "CONNECTED_YOU":
        return ConnectedYouProvider()

    return LocalEsimProvider()


__all__ = [
    "ConnectedYouProvider",
    "EsimProvisioningError",
    "EsimProvisioningResult",
    "EsimProvider",
    "LocalEsimProvider",
    "get_esim_provider",
]
