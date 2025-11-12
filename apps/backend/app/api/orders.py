import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models import User, Order, Payment, EsimProfile, Plan
from ..models.auth_models import OrderStatus, EsimStatus, PaymentProvider, PaymentStatus
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
    plan_id: int, currency: str = "USD", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> OrderRead:
    """Create a new order for a plan."""
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    amount_minor_units = 9900

    order = Order(
        user_id=current_user.id,
        plan_id=plan_id,
        status=OrderStatus.CREATED,
        currency=currency,
        amount_minor_units=amount_minor_units,
    )
    db.add(order)
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
    order_id: int, provider: str = "MOCK", current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Create a payment for an order. For MOCK provider, immediately succeed."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if provider.upper() == "MOCK":
        payment = Payment(
            order_id=order_id,
            provider=PaymentProvider.MOCK,
            status=PaymentStatus.SUCCEEDED,
            raw_payload={"mock": True},
        )
        db.add(payment)
        order.status = OrderStatus.PAID
        db.commit()
        return {"status": "succeeded", "provider": "MOCK"}
    else:
        raise HTTPException(status_code=400, detail="Only MOCK provider supported in dev")


@payments_router.post("/webhook")
def payment_webhook(data: dict, db: Session = Depends(get_db)):
    """Handle payment webhooks from providers. For MOCK, accept any order_id."""
    order_id = data.get("order_id")
    provider_str = data.get("provider", "MOCK")
    status_str = data.get("status", "succeeded")

    if not order_id:
        raise HTTPException(status_code=400, detail="Missing order_id")

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        provider = PaymentProvider[provider_str.upper()]
        status_enum = PaymentStatus.SUCCEEDED if status_str == "succeeded" else PaymentStatus.FAILED
    except KeyError:
        raise HTTPException(status_code=400, detail="Invalid provider or status")

    payment = Payment(order_id=order_id, provider=provider, status=status_enum, raw_payload=data)
    db.add(payment)
    if status_enum == PaymentStatus.SUCCEEDED:
        order.status = OrderStatus.PAID
    db.commit()

    return {"status": "ok"}


@esims_router.post("/activate")
def activate_esim(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> EsimProfileRead:
    """Create an eSIM profile stub for an order."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Check if order is paid
    if order.status != OrderStatus.PAID:
        raise HTTPException(status_code=400, detail="Order must be paid before activating eSIM")

    activation_code = str(uuid.uuid4())

    esim = EsimProfile(
        user_id=current_user.id,
        order_id=order_id,
        country_id=1,
        carrier_id=1,
        plan_id=order.plan_id,
        activation_code=activation_code,
        status=EsimStatus.PENDING,
    )
    db.add(esim)
    db.commit()
    db.refresh(esim)

    return EsimProfileRead.model_validate(esim)
