import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models import User, Order, Payment, EsimProfile, Plan
from ..models.auth_models import OrderStatus, EsimStatus, PaymentProvider, PaymentStatus
from ..services.payment_providers import get_payment_provider
from .auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
esims_router = APIRouter(prefix="/esims", tags=["esims"])


class OrderRead(BaseModel):
    id: int
    plan_id: Optional[int]
    status: str
    currency: str
    amount_minor_units: int
    created_at: datetime

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


@router.post("")
def create_order(
    plan_id: int,
    currency: str = "USD",
    idempotency_key: str | None = Header(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OrderRead:
    """Create a new order for a plan. Uses Idempotency-Key header for deduplication."""
    
    # Check for existing order with same idempotency key
    if idempotency_key:
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
        if existing:
            return OrderRead.model_validate(existing)
    
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    amount_minor_units = 9900

    # Atomic transaction: create Order + pre-register EsimProfile
    order = Order(
        user_id=current_user.id,
        plan_id=plan_id,
        status=OrderStatus.CREATED,
        currency=currency,
        amount_minor_units=amount_minor_units,
        idempotency_key=idempotency_key,
    )
    db.add(order)
    db.flush()  # Get order.id without committing
    
    # Pre-register eSIM profile
    esim = EsimProfile(
        order_id=order.id,
        status=EsimStatus.PENDING,
    )
    db.add(esim)
    db.commit()
    db.refresh(order)

    return OrderRead.model_validate(order)


@router.get("/mine")
def list_user_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """List all orders for the current user."""
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "plan_id": o.plan_id,
            "status": o.status.value if isinstance(o.status, OrderStatus) else o.status,
            "currency": o.currency,
            "amount_minor_units": o.amount_minor_units,
            "created_at": o.created_at,
        }
        for o in orders
    ]


@payments_router.post("/create")
def create_payment(
    order_id: int,
    provider: str = "MOCK",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a payment intent using configured payment provider."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Get provider instance
    payment_provider = get_payment_provider(provider)
    
    # Create payment intent
    intent = payment_provider.create_intent(
        amount_minor_units=int(order.amount_minor_units),  # type: ignore
        currency=str(order.currency),  # type: ignore
        metadata={"order_id": order.id, "user_id": current_user.id}
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
    db.commit()
    
    return {
        "intent_id": intent.intent_id,
        "status": intent.status,
        "provider": provider,
        "amount_minor_units": intent.amount_minor_units,
        "currency": intent.currency
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
def activate_esim(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> EsimProfileRead:
    """Activate eSIM profile with UUID activation code."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if order is paid (type: ignore for SQLAlchemy comparison)
    if order.status != OrderStatus.PAID:  # type: ignore
        raise HTTPException(status_code=400, detail="Order must be paid before activating eSIM")

    # Find pre-registered eSIM profile (created during order)
    esim = db.query(EsimProfile).filter(EsimProfile.order_id == order_id).first()
    if not esim:
        raise HTTPException(status_code=404, detail="eSIM profile not found")
    
    # Generate UUID v4 activation code
    esim.activation_code = str(uuid.uuid4())  # type: ignore
    esim.iccid = f"89001{uuid.uuid4().hex[:17]}"  # type: ignore
    esim.status = EsimStatus.READY  # type: ignore
    esim.user_id = current_user.id  # type: ignore
    esim.country_id = 1  # type: ignore
    esim.carrier_id = 1  # type: ignore
    
    db.commit()
    db.refresh(esim)

    return EsimProfileRead.model_validate(esim)
