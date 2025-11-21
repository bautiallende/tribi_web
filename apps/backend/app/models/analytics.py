import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .auth_models import utcnow
from .catalog import Base


class AnalyticsEventType(enum.Enum):
    USER_SIGNUP = "user_signup"
    CHECKOUT_STARTED = "checkout_started"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    ESIM_ACTIVATED = "esim_activated"


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(AnalyticsEventType), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True, index=True)
    amount_minor_units = Column(BigInteger, nullable=True)
    currency = Column(String(8), default="USD", nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    occurred_at = Column(DateTime, nullable=False, default=utcnow, index=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    user = relationship("User", backref="analytics_events")
    order = relationship("Order", backref="analytics_events")
    plan = relationship("Plan", backref="analytics_events")
