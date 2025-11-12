from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
    BigInteger,
    JSON,
)
from sqlalchemy.orm import relationship
from .catalog import Base
import enum


class PaymentProvider(enum.Enum):
    STRIPE = "STRIPE"
    MERCADO_PAGO = "MERCADO_PAGO"
    MOCK = "MOCK"


class PaymentStatus(enum.Enum):
    REQUIRES_ACTION = "requires_action"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class OrderStatus(enum.Enum):
    CREATED = "created"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class EsimStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    auth_codes = relationship("AuthCode", back_populates="user")
    orders = relationship("Order", back_populates="user")
    esim_profiles = relationship("EsimProfile", back_populates="user")


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Nullable for pre-user codes
    email = Column(String(255), nullable=False, index=True)  # Store email for rate limiting
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    attempts = Column(Integer, default=0)

    user = relationship("User", back_populates="auth_codes")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.CREATED, nullable=False)
    currency = Column(String(8), nullable=False, default="USD")
    amount_minor_units = Column(BigInteger, nullable=False)
    provider_ref = Column(String(255), nullable=True)
    idempotency_key = Column(String(255), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    plan = relationship("Plan")
    payments = relationship("Payment", back_populates="order")
    esim_profile = relationship("EsimProfile", back_populates="order", uselist=False)


class EsimProfile(Base):
    __tablename__ = "esim_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True, index=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True, index=True)
    activation_code = Column(String(128), nullable=False)
    iccid = Column(String(64), nullable=True)
    status = Column(Enum(EsimStatus), default=EsimStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="esim_profiles")
    order = relationship("Order", back_populates="esim_profile")
    country = relationship("Country")
    carrier = relationship("Carrier")
    plan = relationship("Plan")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    provider = Column(Enum(PaymentProvider), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    intent_id = Column(String(255), nullable=True, unique=True, index=True)  # Provider's payment intent ID
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payments")

    order = relationship("Order", back_populates="payments")
