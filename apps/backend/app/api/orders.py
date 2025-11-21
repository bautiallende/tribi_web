import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, joinedload

from ..core.config import settings
from ..db.session import get_db
from ..models import EsimInventory, EsimProfile, Order, Payment, Plan, User
from ..models.auth_models import (
    EsimInventoryStatus,
    EsimStatus,
    OrderStatus,
    PaymentStatus,
)
from ..models.auth_models import (
    PaymentProvider as PaymentProviderEnum,
)
from ..services.analytics import AnalyticsEventType, record_event
from ..services.billing import generate_invoice_for_order
from ..services.esim_inventory import (
    create_inventory_from_provisioning,
    reserve_inventory_item,
    result_from_inventory_item,
)
from ..services.esim_providers import (
    EsimProvisioningError,
    EsimProvisioningResult,
    get_esim_provider,
)
from ..services.payment_providers import (
    PaymentWebhookValidationError,
    get_payment_provider,
)
from ..services.pricing import format_minor_units, to_minor_units
from .auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])
payments_router = APIRouter(prefix="/api/payments", tags=["payments"])
esims_router = APIRouter(prefix="/api/esims", tags=["esims"])
logger = logging.getLogger(__name__)
DEFAULT_ESIM_INSTRUCTIONS = "Install via Settings > Cellular > Add eSIM and scan the QR or enter the activation code manually."


def _apply_provisioning_to_esim(
    *,
    esim: EsimProfile,
    provisioning_result: EsimProvisioningResult,
    inventory_item: EsimInventory | None,
) -> None:
    """Persist provisioning data onto the EsimProfile and optional inventory row."""

    activation_code = (
        provisioning_result.activation_code or esim.activation_code or str(uuid.uuid4())
    )
    iccid = provisioning_result.iccid or esim.iccid or f"89001{uuid.uuid4().hex[:17]}"
    qr_payload = (
        provisioning_result.qr_payload or esim.qr_payload or f"LPA:1${activation_code}"
    )
    instructions = (
        provisioning_result.instructions
        or esim.instructions
        or DEFAULT_ESIM_INSTRUCTIONS
    )

    esim.activation_code = activation_code  # type: ignore[assignment]
    esim.iccid = iccid  # type: ignore[assignment]
    esim.qr_payload = qr_payload  # type: ignore[assignment]
    esim.instructions = instructions  # type: ignore[assignment]
    esim.status = EsimStatus.ACTIVE  # type: ignore[assignment]
    esim.provider_reference = provisioning_result.provider_reference or esim.provider_reference  # type: ignore[assignment]
    esim.provider_payload = provisioning_result.metadata  # type: ignore[assignment]
    esim.provisioned_at = datetime.utcnow()  # type: ignore[assignment]

    if inventory_item:
        inventory_item.activation_code = (
            inventory_item.activation_code or activation_code
        )  # type: ignore[assignment]
        inventory_item.iccid = inventory_item.iccid or iccid  # type: ignore[assignment]
        inventory_item.qr_payload = inventory_item.qr_payload or qr_payload  # type: ignore[assignment]
        inventory_item.instructions = inventory_item.instructions or instructions  # type: ignore[assignment]
        inventory_item.status = EsimInventoryStatus.ASSIGNED  # type: ignore[assignment]
        inventory_item.assigned_at = inventory_item.assigned_at or datetime.utcnow()  # type: ignore[assignment]
        esim.inventory_item = inventory_item  # type: ignore[assignment]
        esim.inventory_item_id = inventory_item.id  # type: ignore[assignment]


class PlanSnapshot(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    country_name: Optional[str] = None
    country_iso2: Optional[str] = None
    carrier_name: Optional[str] = None
    country_id: Optional[int] = None
    carrier_id: Optional[int] = None
    data_gb: Optional[float] = None
    duration_days: Optional[int] = None
    price_minor_units: Optional[int] = None
    currency: Optional[str] = None


class OrderRead(BaseModel):
    id: int
    plan_id: Optional[int]
    status: str
    currency: str
    amount_minor_units: int
    amount_major: str
    created_at: datetime
    plan_snapshot: Optional[PlanSnapshot] = None
    esim_profile: Optional["EsimProfileRead"] = None


class OrderCreateRequest(BaseModel):
    plan_id: int
    currency: str = "USD"


class PaymentCreateRequest(BaseModel):
    order_id: int
    provider: str | None = None


class EsimActivateRequest(BaseModel):
    order_id: int


class EsimProfileRead(BaseModel):
    id: int
    order_id: Optional[int]
    activation_code: Optional[str]
    iccid: Optional[str]
    status: str
    created_at: datetime
    provisioned_at: Optional[datetime] = None
    provider_reference: Optional[str] = None
    qr_payload: Optional[str] = None
    instructions: Optional[str] = None
    provider_payload: Optional[dict[str, Any]] = None
    inventory_item_id: Optional[int] = None
    plan_id: Optional[int] = None
    country_id: Optional[int] = None
    carrier_id: Optional[int] = None
    plan_snapshot: Optional[PlanSnapshot] = None
    model_config = ConfigDict(from_attributes=True)


try:  # Maintain compatibility across Pydantic versions
    OrderRead.model_rebuild()  # type: ignore[attr-defined]
except AttributeError:  # pragma: no cover - executed on Pydantic v1
    OrderRead.update_forward_refs()


def _build_plan_snapshot(plan: Plan | None, currency: str) -> dict[str, Any] | None:
    if plan is None:
        return None

    plan_price = (
        cast(Decimal, plan.price_usd) if plan.price_usd is not None else Decimal("0")
    )
    amount_minor_units = to_minor_units(plan_price)
    data_gb_value = (
        float(cast(Decimal, plan.data_gb)) if plan.data_gb is not None else None
    )

    return {
        "id": plan.id,
        "name": plan.name,
        "description": plan.description,
        "country_name": plan.country.name if plan.country else None,
        "country_iso2": plan.country.iso2 if plan.country else None,
        "country_id": plan.country_id,
        "carrier_id": plan.carrier_id,
        "carrier_name": plan.carrier.name if plan.carrier else None,
        "data_gb": data_gb_value,
        "duration_days": plan.duration_days,
        "price_minor_units": amount_minor_units,
        "currency": currency,
    }


def serialize_order(order: Order) -> dict[str, Any]:
    amount_minor_units = (
        cast(int, order.amount_minor_units)
        if order.amount_minor_units is not None
        else 0
    )
    currency = str(order.currency or "USD")
    price_info = format_minor_units(amount_minor_units, currency)
    status = (
        order.status.value if isinstance(order.status, OrderStatus) else order.status
    )
    plan_snapshot_db = getattr(order, "plan_snapshot", None)
    plan_snapshot: dict[str, Any] | None = cast(dict[str, Any] | None, plan_snapshot_db)
    if plan_snapshot is None:
        plan_snapshot = _build_plan_snapshot(order.plan, currency)
    snapshot_payload = plan_snapshot or {}
    esim_data = None
    if getattr(order, "esim_profile", None):
        esim_data = serialize_esim(order.esim_profile, currency, plan_snapshot)
    return {
        "id": order.id,
        "plan_id": order.plan_id,
        "status": status,
        "currency": currency,
        "amount_minor_units": amount_minor_units,
        "amount_major": price_info["amount_major"],
        "created_at": order.created_at,
        "plan_snapshot": snapshot_payload,
        "esim_profile": esim_data,
    }


def serialize_esim(
    esim: EsimProfile,
    default_currency: str | None = "USD",
    default_plan_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = esim.status.value if isinstance(esim.status, EsimStatus) else esim.status
    currency = default_currency or "USD"
    order_snapshot: dict[str, Any] | None = None
    if getattr(esim, "order", None):
        currency = str(esim.order.currency or currency)
        plan_snapshot_candidate = getattr(esim.order, "plan_snapshot", None)
        if plan_snapshot_candidate is not None:
            order_snapshot = cast(dict[str, Any] | None, plan_snapshot_candidate)
        elif getattr(esim.order, "plan", None):
            order_snapshot = _build_plan_snapshot(esim.order.plan, currency)

    plan_snapshot = (
        default_plan_snapshot
        or order_snapshot
        or _build_plan_snapshot(getattr(esim, "plan", None), currency)
        or None
    )

    return {
        "id": esim.id,
        "order_id": esim.order_id,
        "activation_code": esim.activation_code,
        "iccid": esim.iccid,
        "status": status,
        "created_at": esim.created_at,
        "provisioned_at": getattr(esim, "provisioned_at", None),
        "provider_reference": getattr(esim, "provider_reference", None),
        "provider_payload": getattr(esim, "provider_payload", None),
        "qr_payload": esim.qr_payload,
        "instructions": esim.instructions,
        "inventory_item_id": getattr(esim, "inventory_item_id", None),
        "plan_id": esim.plan_id,
        "country_id": esim.country_id,
        "carrier_id": esim.carrier_id,
        "plan_snapshot": plan_snapshot,
    }


def _map_payment_status(status: str | None) -> PaymentStatus:
    normalized = (status or PaymentStatus.REQUIRES_ACTION.value).lower()
    if normalized == PaymentStatus.SUCCEEDED.value:
        return PaymentStatus.SUCCEEDED
    if normalized == PaymentStatus.FAILED.value:
        return PaymentStatus.FAILED
    return PaymentStatus.REQUIRES_ACTION


def _update_order_status_from_payment(
    order: Order | None, payment_status: PaymentStatus
) -> None:
    if not order:
        return
    if payment_status == PaymentStatus.SUCCEEDED:
        order.status = OrderStatus.PAID  # type: ignore[assignment]
    elif payment_status == PaymentStatus.FAILED:
        order.status = OrderStatus.FAILED  # type: ignore[assignment]


def _maybe_issue_invoice(
    db: Session,
    *,
    order: Order | None,
    payment_status: PaymentStatus,
    payment: Payment | None,
) -> None:
    if not order or payment_status != PaymentStatus.SUCCEEDED:
        return

    try:
        generate_invoice_for_order(db, order=order, payment=payment)
    except Exception as exc:  # pragma: no cover - log + continue
        logger.error("Failed to generate invoice for order %s: %s", order.id, exc)


def _record_payment_success_event(
    db: Session,
    *,
    order: Order | None,
    payment: Payment,
) -> None:
    if not order:
        return

    amount_minor_units = int(order.amount_minor_units or 0)
    record_event(
        db,
        event_type=AnalyticsEventType.PAYMENT_SUCCEEDED,
        user_id=cast(int, order.user_id),
        order_id=cast(int, order.id),
        plan_id=order.plan_id,
        amount_minor_units=amount_minor_units,
        currency=str(order.currency or settings.DEFAULT_CURRENCY),
        metadata={
            "payment_id": payment.id,
            "provider": (
                payment.provider.value
                if isinstance(payment.provider, PaymentProviderEnum)
                else str(payment.provider)
            ),
            "intent_id": payment.intent_id,
        },
    )


@router.post("", response_model=OrderRead)
def create_order(
    payload: OrderCreateRequest,
    idempotency_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrderRead:
    """Create a new order for a plan. Uses Idempotency-Key header for deduplication."""
    plan_id = payload.plan_id
    currency = payload.currency or "USD"

    # Check for existing order with same idempotency key
    normalized_key = None
    if idempotency_key:
        normalized_key = f"{current_user.id}:{idempotency_key}"
        existing = (
            db.query(Order).filter(Order.idempotency_key == normalized_key).first()
        )
        if existing:
            return OrderRead(**serialize_order(existing))

    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan_snapshot = _build_plan_snapshot(plan, currency) or {}
    amount_minor_units = int(plan_snapshot.get("price_minor_units", 0))
    if amount_minor_units <= 0:
        plan_price = (
            cast(Decimal, plan.price_usd)
            if plan.price_usd is not None
            else Decimal("0")
        )
        amount_minor_units = to_minor_units(plan_price)

    # Atomic transaction: create Order + pre-register EsimProfile
    order = Order(
        user_id=cast(int, current_user.id),
        plan_id=plan_id,
        status=OrderStatus.CREATED,
        currency=currency,
        amount_minor_units=amount_minor_units,
        idempotency_key=normalized_key,
        plan_snapshot=plan_snapshot,
    )
    db.add(order)
    db.flush()  # Get order.id without committing

    # Pre-register eSIM profile
    esim = EsimProfile(
        order=order,
        status=EsimStatus.PENDING_ACTIVATION,
        user_id=current_user.id,
        plan_id=plan_id,
        country_id=plan.country_id,
        carrier_id=plan.carrier_id,
    )
    db.add(esim)
    record_event(
        db,
        event_type=AnalyticsEventType.CHECKOUT_STARTED,
        user_id=current_user.id,
        order_id=cast(int, order.id),
        plan_id=plan_id,
        amount_minor_units=amount_minor_units,
        currency=currency,
        metadata={
            "plan_snapshot": plan_snapshot,
            "idempotency_key": normalized_key,
        },
    )
    db.commit()
    db.refresh(order)

    return OrderRead(**serialize_order(order))


@router.get("/mine", response_model=list[OrderRead])
def list_user_orders(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """List all orders for the current user."""
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.plan),
            joinedload(Order.esim_profile).joinedload(EsimProfile.plan),
        )
        .filter(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [serialize_order(o) for o in orders]


@payments_router.post("/create")
def create_payment(
    payload: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(None),
):
    """Create a payment intent using configured payment provider."""
    order_id = payload.order_id
    provider_name = (payload.provider or settings.PAYMENT_PROVIDER).upper()
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        provider_enum = PaymentProviderEnum[provider_name]
    except KeyError as exc:
        raise HTTPException(
            status_code=400, detail="Unsupported payment provider"
        ) from exc

    # Get provider instance
    try:
        payment_provider = get_payment_provider(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    provider_idempotency_key = None
    if idempotency_key:
        provider_idempotency_key = f"{current_user.id}:{idempotency_key}"

    # Create payment intent
    intent = payment_provider.create_intent(
        amount_minor_units=int(order.amount_minor_units),  # type: ignore
        currency=str(order.currency or settings.DEFAULT_CURRENCY),
        metadata={"order_id": order.id, "user_id": current_user.id},
        idempotency_key=provider_idempotency_key,
    )

    payment_status = _map_payment_status(intent.status)

    # Store payment record
    payment = Payment(
        order_id=order_id,
        provider=provider_enum,
        status=payment_status,
        intent_id=intent.intent_id,
        raw_payload={"intent": intent.intent_id, "metadata": intent.metadata},
    )
    db.add(payment)
    _update_order_status_from_payment(order, payment_status)
    _maybe_issue_invoice(
        db, order=order, payment_status=payment_status, payment=payment
    )
    if payment_status == PaymentStatus.SUCCEEDED:
        _record_payment_success_event(db, order=order, payment=payment)
    db.commit()

    response_payload = {
        "intent_id": intent.intent_id,
        "status": intent.status,
        "provider": provider_name,
        "amount_minor_units": intent.amount_minor_units,
        "currency": intent.currency,
    }

    if intent.client_secret:
        response_payload["client_secret"] = intent.client_secret
        response_payload["publishable_key"] = settings.STRIPE_PUBLISHABLE_KEY

    return response_payload


@payments_router.post("/webhook")
async def payment_webhook(
    request: Request,
    provider: str | None = None,
    db: Session = Depends(get_db),
):
    """Handle payment webhooks from providers."""
    provider_name = (provider or settings.PAYMENT_PROVIDER).upper()

    try:
        payment_provider = get_payment_provider(provider_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    raw_body = await request.body()
    headers = dict(request.headers)

    try:
        payload = payment_provider.parse_webhook_payload(raw_body, headers)
    except PaymentWebhookValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    intent = payment_provider.process_webhook(payload)

    if not intent.intent_id:
        raise HTTPException(status_code=400, detail="Missing intent_id")

    payment = db.query(Payment).filter(Payment.intent_id == intent.intent_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Update payment status
    previous_status = (
        payment.status
        if isinstance(payment.status, PaymentStatus)
        else PaymentStatus(payment.status)
    )
    payment_status = _map_payment_status(intent.status)
    setattr(payment, "status", payment_status)
    setattr(payment, "raw_payload", payload)

    # Update order status based on payment
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    _update_order_status_from_payment(order, payment_status)
    _maybe_issue_invoice(
        db, order=order, payment_status=payment_status, payment=payment
    )
    if (
        payment_status == PaymentStatus.SUCCEEDED
        and previous_status != PaymentStatus.SUCCEEDED
    ):
        _record_payment_success_event(db, order=order, payment=payment)

    db.commit()

    return {"status": "processed", "intent_status": intent.status}


@esims_router.post("/activate")
def activate_esim(
    payload: EsimActivateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EsimProfileRead:
    """Activate eSIM profile with UUID activation code."""
    order_id = payload.order_id
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if order is paid (type: ignore for SQLAlchemy comparison)
    if order.status != OrderStatus.PAID:  # type: ignore
        raise HTTPException(
            status_code=400, detail="Order must be paid before activating eSIM"
        )

    # Find pre-registered eSIM profile (created during order)
    esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
    if not esim:
        raise HTTPException(status_code=404, detail="eSIM profile not found")

    esim_status = (
        esim.status if isinstance(esim.status, EsimStatus) else EsimStatus(esim.status)
    )

    if esim.provisioned_at or esim_status in {EsimStatus.ASSIGNED, EsimStatus.ACTIVE}:  # type: ignore[arg-type]
        # Already provisioned, return existing payload idempotently.
        return EsimProfileRead(**serialize_esim(esim))

    if esim_status not in {EsimStatus.PENDING_ACTIVATION, EsimStatus.RESERVED}:
        raise HTTPException(
            status_code=400,
            detail="eSIM already activated or not ready for activation",
        )

    plan_snapshot = cast(dict[str, Any], order.plan_snapshot or {})
    plan_id = cast(
        Optional[int], getattr(esim, "plan_id", None) or getattr(order, "plan_id", None)
    )
    country_id = cast(
        Optional[int],
        getattr(esim, "country_id", None) or plan_snapshot.get("country_id"),
    )
    carrier_id = cast(
        Optional[int],
        getattr(esim, "carrier_id", None) or plan_snapshot.get("carrier_id"),
    )

    inventory_item = reserve_inventory_item(
        db,
        plan_id=plan_id,
        country_id=country_id,
        carrier_id=carrier_id,
    )

    provisioning_result: EsimProvisioningResult
    if inventory_item:
        provisioning_result = result_from_inventory_item(inventory_item)
    else:
        provider = get_esim_provider()
        try:
            provisioning_result = provider.provision(order=order, profile=esim)
        except EsimProvisioningError as exc:
            logger.error("eSIM provisioning failed for order %s: %s", order.id, exc)
            raise HTTPException(
                status_code=502, detail="Unable to provision eSIM"
            ) from exc

        inventory_item = create_inventory_from_provisioning(
            db,
            plan_id=plan_id,
            country_id=country_id,
            carrier_id=carrier_id,
            provisioning_result=provisioning_result,
        )

    _apply_provisioning_to_esim(
        esim=esim,
        provisioning_result=provisioning_result,
        inventory_item=inventory_item,
    )
    record_event(
        db,
        event_type=AnalyticsEventType.ESIM_ACTIVATED,
        user_id=cast(int, current_user.id),
        order_id=cast(int, order.id),
        plan_id=plan_id,
        metadata={
            "inventory_item_id": getattr(inventory_item, "id", None),
            "country_id": country_id,
            "carrier_id": carrier_id,
            "provider_reference": provisioning_result.provider_reference,
        },
    )

    db.commit()
    db.refresh(esim)

    return EsimProfileRead(**serialize_esim(esim))


@esims_router.get("/mine", response_model=list[EsimProfileRead])
def list_my_esims(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    esims = (
        db.query(EsimProfile)
        .filter(EsimProfile.user_id == current_user.id)
        .options(
            joinedload(EsimProfile.order).joinedload(Order.plan),
            joinedload(EsimProfile.plan),
        )
        .order_by(EsimProfile.created_at.desc())
        .all()
    )
    return [EsimProfileRead(**serialize_esim(esim)) for esim in esims]


@esims_router.get("/{esim_id}", response_model=EsimProfileRead)
def get_esim_detail(
    esim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    esim = (
        db.query(EsimProfile)
        .filter(EsimProfile.id == esim_id, EsimProfile.user_id == current_user.id)
        .options(
            joinedload(EsimProfile.order).joinedload(Order.plan),
            joinedload(EsimProfile.plan),
        )
        .first()
    )
    if not esim:
        raise HTTPException(status_code=404, detail="eSIM profile not found")

    return EsimProfileRead(**serialize_esim(esim))
