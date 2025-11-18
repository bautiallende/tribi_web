import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, cast

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session, joinedload

from ..db.session import get_db
from ..models import EsimProfile, Order, Payment, Plan, User
from ..models.auth_models import EsimStatus, OrderStatus, PaymentProvider, PaymentStatus
from ..services.payment_providers import get_payment_provider
from ..services.pricing import format_minor_units, to_minor_units
from .auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])
payments_router = APIRouter(prefix="/api/payments", tags=["payments"])
esims_router = APIRouter(prefix="/api/esims", tags=["esims"])


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
    provider: str = "MOCK"


class EsimActivateRequest(BaseModel):
    order_id: int


class EsimProfileRead(BaseModel):
    id: int
    order_id: Optional[int]
    activation_code: Optional[str]
    iccid: Optional[str]
    status: str
    created_at: datetime
    qr_payload: Optional[str] = None
    instructions: Optional[str] = None
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
        "qr_payload": esim.qr_payload,
        "instructions": esim.instructions,
        "plan_id": esim.plan_id,
        "country_id": esim.country_id,
        "carrier_id": esim.carrier_id,
        "plan_snapshot": plan_snapshot,
    }


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
        user_id=current_user.id,
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
):
    """Create a payment intent using configured payment provider."""
    order_id = payload.order_id
    provider = payload.provider
    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get provider instance
    payment_provider = get_payment_provider(provider)

    # Create payment intent
    intent = payment_provider.create_intent(
        amount_minor_units=int(order.amount_minor_units),  # type: ignore
        currency=str(order.currency),  # type: ignore
        metadata={"order_id": order.id, "user_id": current_user.id},
    )

    # Store payment record
    payment = Payment(
        order_id=order_id,
        provider=PaymentProvider[provider.upper()],
        status=PaymentStatus[intent.status.upper()],
        intent_id=intent.intent_id,
        raw_payload={"intent": intent.intent_id, "metadata": intent.metadata},
    )
    db.add(payment)
    if intent.status == "succeeded":
        order.status = OrderStatus.PAID  # type: ignore
    db.commit()

    return {
        "intent_id": intent.intent_id,
        "status": intent.status,
        "provider": provider,
        "amount_minor_units": intent.amount_minor_units,
        "currency": intent.currency,
    }


@payments_router.post("/webhook")
def payment_webhook(data: dict, db: Session = Depends(get_db)):
    """Handle payment webhooks from providers."""
    provider_name = data.get("provider", "MOCK")
    intent_id = data.get("intent_id")

    if not intent_id:
        raise HTTPException(status_code=400, detail="Missing intent_id")

    # Get provider instance
    payment_provider = get_payment_provider(provider_name)

    # Process webhook
    intent = payment_provider.process_webhook(data)

    # Find payment by intent_id
    payment = db.query(Payment).filter(Payment.intent_id == intent_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Update payment status
    payment.status = PaymentStatus[intent.status.upper()]  # type: ignore

    # Update order status based on payment
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if intent.status == "succeeded":
        order.status = OrderStatus.PAID  # type: ignore
    elif intent.status == "failed":
        order.status = OrderStatus.FAILED  # type: ignore

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

    if esim.status != EsimStatus.PENDING_ACTIVATION:  # type: ignore[comparison-overlap]
        raise HTTPException(
            status_code=400,
            detail="eSIM already activated or not ready for activation",
        )

    activation_code = esim.activation_code or str(uuid.uuid4())
    esim.activation_code = activation_code  # type: ignore[assignment]
    if esim.iccid is None:
        esim.iccid = f"89001{uuid.uuid4().hex[:17]}"  # type: ignore[assignment]
    esim.status = EsimStatus.ACTIVE  # type: ignore[assignment]
    if esim.qr_payload is None:
        esim.qr_payload = f"LPA:1${activation_code}"  # type: ignore[assignment]
    if esim.instructions is None:
        instruction_text = (
            "Install via Settings > Cellular > Add eSIM and scan the QR "
            "or enter the activation code manually."
        )
        setattr(esim, "instructions", instruction_text)

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
