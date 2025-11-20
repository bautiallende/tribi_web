from types import SimpleNamespace

import pytest
from app.services.esim_providers import (
    ConnectedYouProvider,
    EsimProvisioningError,
    LocalEsimProvider,
)


def _order_fixture():
    return SimpleNamespace(
        id=101,
        plan_id=55,
        currency="USD",
        plan_snapshot={
            "name": "Global Week Pass",
            "country_iso2": "US",
            "carrier_name": "Connected Carrier",
            "external_id": "PLAN-55",
        },
        user=SimpleNamespace(email="user@example.com", name="Test User"),
    )


def _profile_fixture():
    return SimpleNamespace(
        activation_code=None,
        iccid=None,
        qr_payload=None,
        instructions=None,
        user=SimpleNamespace(name="Test User"),
        country=None,
    )


def test_local_provider_generates_codes():
    provider = LocalEsimProvider()
    result = provider.provision(order=_order_fixture(), profile=_profile_fixture())

    assert result.activation_code.startswith("LOCAL-")
    assert result.metadata == {"provider": "LOCAL"}
    assert result.qr_payload and result.qr_payload.startswith("LPA:1$")


def test_connected_you_provider_dry_run_builds_payload():
    provider = ConnectedYouProvider(
        base_url="https://sandbox.api.connectedyou.com",
        api_key="dummy-key",
        partner_id="partner-1",
        dry_run=True,
    )

    result = provider.provision(order=_order_fixture(), profile=_profile_fixture())

    assert result.metadata
    assert result.metadata["provider"] == "CONNECTED_YOU"
    assert "dry_run_payload" in result.metadata
    assert result.provider_reference == "order-101"


def test_connected_you_provider_requires_api_key_when_not_dry_run():
    with pytest.raises(EsimProvisioningError):
        ConnectedYouProvider(
            base_url="https://sandbox.api.connectedyou.com",
            partner_id="partner-1",
            api_key=None,
            dry_run=False,
        )
