"""Helpers for reserving and assigning eSIM inventory items."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..models import EsimInventory
from ..models.auth_models import EsimInventoryStatus
from .esim_providers import EsimProvisioningResult


def reserve_inventory_item(
    db: Session,
    *,
    plan_id: Optional[int],
    country_id: Optional[int],
    carrier_id: Optional[int],
) -> Optional[EsimInventory]:
    """Attempt to reserve (and lock) the next available inventory item."""

    query = db.query(EsimInventory).filter(
        EsimInventory.status == EsimInventoryStatus.AVAILABLE
    )

    if plan_id:
        query = query.filter(EsimInventory.plan_id == plan_id)
    elif country_id:
        query = query.filter(EsimInventory.country_id == country_id)
    elif carrier_id:
        query = query.filter(EsimInventory.carrier_id == carrier_id)

    item = query.order_by(EsimInventory.id).with_for_update(skip_locked=True).first()

    if item:
        item.status = EsimInventoryStatus.RESERVED
        item.reserved_at = datetime.utcnow()

    return item


def result_from_inventory_item(inventory_item: EsimInventory) -> EsimProvisioningResult:
    """Normalize an inventory row into an EsimProvisioningResult payload."""

    return EsimProvisioningResult(
        activation_code=inventory_item.activation_code or "",
        iccid=inventory_item.iccid,
        qr_payload=inventory_item.qr_payload,
        instructions=inventory_item.instructions,
        provider_reference=inventory_item.provider_reference,
        metadata={
            "provider": "INVENTORY",
            "inventory_id": inventory_item.id,
            "provider_payload": inventory_item.provider_payload,
        },
    )


def create_inventory_from_provisioning(
    db: Session,
    *,
    plan_id: Optional[int],
    country_id: Optional[int],
    carrier_id: Optional[int],
    provisioning_result: EsimProvisioningResult,
) -> EsimInventory:
    """Persist a synthetic inventory row based on a provider response."""

    item = EsimInventory(
        plan_id=plan_id,
        country_id=country_id,
        carrier_id=carrier_id,
        activation_code=provisioning_result.activation_code,
        iccid=provisioning_result.iccid,
        qr_payload=provisioning_result.qr_payload,
        instructions=provisioning_result.instructions,
        status=EsimInventoryStatus.ASSIGNED,
        assigned_at=datetime.utcnow(),
        provider_reference=provisioning_result.provider_reference,
        provider_payload=provisioning_result.metadata,
    )

    db.add(item)
    db.flush()
    return item


__all__ = [
    "reserve_inventory_item",
    "result_from_inventory_item",
    "create_inventory_from_provisioning",
]
