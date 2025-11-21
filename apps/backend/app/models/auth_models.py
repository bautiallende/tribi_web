import datetime as dt
import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .catalog import Base


def utcnow() -> dt.datetime:
    return dt.datetime.utcnow()


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
    DRAFT = "draft"
    PENDING_ACTIVATION = "pending_activation"
    RESERVED = "reserved"
    ASSIGNED = "assigned"
    ACTIVE = "active"
    FAILED = "failed"
    EXPIRED = "expired"


class EsimInventoryStatus(enum.Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    ASSIGNED = "assigned"
    RETIRED = "retired"


class SupportTicketStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ARCHIVED = "archived"


class SupportTicketPriority(enum.Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class SupportTicketEventType(enum.Enum):
    CREATED = "created"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    NOTE_ADDED = "note_added"
    REMINDER_SENT = "reminder_sent"
    ESCALATED = "escalated"
    SLA_UPDATED = "sla_updated"


class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    ISSUED = "issued"
    VOID = "void"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    last_login = Column(DateTime, nullable=True)
    internal_notes = Column(Text, nullable=True)

    auth_codes = relationship("AuthCode", back_populates="user")
    orders = relationship("Order", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    support_tickets = relationship("SupportTicket", back_populates="user")
    esim_profiles = relationship("EsimProfile", back_populates="user")


class AuthCode(Base):
    __tablename__ = "auth_codes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )  # Nullable for pre-user codes
    email = Column(
        String(255), nullable=False, index=True
    )  # Store email for rate limiting
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    created_at = Column(DateTime, default=utcnow, index=True)
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
    created_at = Column(DateTime, default=utcnow)
    plan_snapshot = Column(JSON, nullable=True)

    user = relationship("User", back_populates="orders")
    plan = relationship("Plan")
    payments = relationship("Payment", back_populates="order")
    esim_profile = relationship("EsimProfile", back_populates="order", uselist=False)
    invoice = relationship("Invoice", back_populates="order", uselist=False)
    support_tickets = relationship("SupportTicket", back_populates="order")


class EsimProfile(Base):
    __tablename__ = "esim_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True, index=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True, index=True)
    inventory_item_id = Column(
        Integer, ForeignKey("esim_inventory.id"), nullable=True, index=True
    )
    activation_code = Column(String(128), nullable=True)
    iccid = Column(String(64), nullable=True)
    status = Column(
        Enum(
            EsimStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=EsimStatus.PENDING_ACTIVATION,
        nullable=False,
    )
    provider_reference = Column(String(128), nullable=True)
    provisioned_at = Column(DateTime, nullable=True)
    provider_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    qr_payload = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)

    user = relationship("User", back_populates="esim_profiles")
    order = relationship("Order", back_populates="esim_profile")
    country = relationship("Country")
    carrier = relationship("Carrier")
    plan = relationship("Plan")
    inventory_item = relationship(
        "EsimInventory", back_populates="profiles", foreign_keys=[inventory_item_id]
    )


class EsimInventory(Base):
    __tablename__ = "esim_inventory"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=True, index=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True, index=True)
    activation_code = Column(String(128), nullable=True)
    iccid = Column(String(64), nullable=True)
    qr_payload = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    status = Column(
        Enum(
            EsimInventoryStatus,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        default=EsimInventoryStatus.AVAILABLE,
        nullable=False,
    )
    extra_metadata = Column("metadata", JSON, nullable=True)
    provider_reference = Column(String(128), nullable=True)
    provider_payload = Column(JSON, nullable=True)
    reserved_at = Column(DateTime, nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    plan = relationship("Plan")
    country = relationship("Country")
    carrier = relationship("Carrier")
    profiles = relationship("EsimProfile", back_populates="inventory_item")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    provider = Column(Enum(PaymentProvider), nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    intent_id = Column(
        String(255), nullable=True, unique=True, index=True
    )  # Provider's payment intent ID
    raw_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    order = relationship("Order", back_populates="payments")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(32), nullable=False, unique=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    currency = Column(String(8), nullable=False, default="USD")
    amount_minor_units = Column(BigInteger, nullable=False, default=0)
    tax_minor_units = Column(BigInteger, nullable=False, default=0)
    status = Column(Enum(InvoiceStatus), default=InvoiceStatus.ISSUED, nullable=False)
    issued_at = Column(DateTime, default=utcnow, nullable=False)
    extra_metadata = Column("metadata", JSON, nullable=True)
    pdf_url = Column(String(512), nullable=True)

    order = relationship("Order", back_populates="invoice")
    user = relationship("User", back_populates="invoices")


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True, index=True)
    status = Column(
        Enum(SupportTicketStatus), default=SupportTicketStatus.OPEN, nullable=False
    )
    priority = Column(
        Enum(SupportTicketPriority),
        default=SupportTicketPriority.NORMAL,
        nullable=False,
    )
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    last_reminder_at = Column(DateTime, nullable=True)
    reminder_count = Column(Integer, default=0, nullable=False)
    escalation_level = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="support_tickets")
    order = relationship("Order", back_populates="support_tickets")
    audit_entries = relationship(
        "SupportTicketAudit",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="SupportTicketAudit.created_at",
    )


class SupportTicketAudit(Base):
    __tablename__ = "support_ticket_audit"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    event_type = Column(Enum(SupportTicketEventType), nullable=False)
    actor = Column(String(255), nullable=True)
    from_status = Column(Enum(SupportTicketStatus), nullable=True)
    to_status = Column(Enum(SupportTicketStatus), nullable=True)
    notes = Column(Text, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    ticket = relationship("SupportTicket", back_populates="audit_entries")
