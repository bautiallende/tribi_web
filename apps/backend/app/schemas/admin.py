from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

# ========================================
# Country Schemas
# ========================================


class CountryCreate(BaseModel):
    iso2: str = Field(..., description="Two-letter country code")
    name: str = Field(..., min_length=1, max_length=255, description="Country name")


class CountryUpdate(BaseModel):
    iso2: str | None = Field(None, description="Two-letter country code")
    name: str | None = Field(
        None, min_length=1, max_length=255, description="Country name"
    )


# ========================================
# Carrier Schemas
# ========================================


class CarrierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Carrier name")


class CarrierUpdate(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=255, description="Carrier name"
    )


# ========================================
# Plan Schemas
# ========================================


class PlanCreate(BaseModel):
    country_id: int = Field(..., gt=0, description="Country ID")
    carrier_id: int = Field(..., gt=0, description="Carrier ID")
    name: str = Field(..., min_length=1, max_length=255, description="Plan name")
    data_gb: float = Field(..., description="Data in GB")
    duration_days: int = Field(..., description="Duration in days")
    price_usd: float = Field(..., description="Price in USD")
    description: str | None = Field(None, description="Plan description")
    is_unlimited: bool = Field(False, description="Is unlimited data")


class PlanUpdate(BaseModel):
    country_id: int | None = Field(None, gt=0, description="Country ID")
    carrier_id: int | None = Field(None, gt=0, description="Carrier ID")
    name: str | None = Field(
        None, min_length=1, max_length=255, description="Plan name"
    )
    data_gb: float | None = Field(None, description="Data in GB")
    duration_days: int | None = Field(None, description="Duration in days")
    price_usd: float | None = Field(None, description="Price in USD")
    description: str | None = Field(None, description="Plan description")
    is_unlimited: bool | None = Field(None, description="Is unlimited data")


# ========================================
# Pagination
# ========================================

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========================================
# Admin Dashboard Entities
# ========================================


class AdminUserSummary(BaseModel):
    id: int
    email: str | None = None
    name: str | None = None


class AdminPaymentRead(BaseModel):
    id: int
    order_id: int
    provider: str
    status: str
    intent_id: str | None = None
    created_at: datetime
    order_amount_minor_units: int
    order_currency: str | None = None


class AdminEsimProfileRead(BaseModel):
    id: int
    order_id: int | None = None
    status: str
    activation_code: str | None = None
    iccid: str | None = None
    inventory_item_id: int | None = None
    plan_id: int | None = None
    country_id: int | None = None
    carrier_id: int | None = None
    provisioned_at: datetime | None = None
    provider_reference: str | None = None
    created_at: datetime


class AdminInventoryRead(BaseModel):
    id: int
    plan_id: int | None = None
    carrier_id: int | None = None
    country_id: int | None = None
    status: str
    activation_code: str | None = None
    iccid: str | None = None
    qr_payload: str | None = None
    instructions: str | None = None
    provider_reference: str | None = None
    reserved_at: datetime | None = None
    assigned_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None


class AdminOrderRead(BaseModel):
    id: int
    status: str
    currency: str
    amount_minor_units: int
    created_at: datetime
    plan_id: int | None = None
    plan_snapshot: dict[str, Any] | None = None
    user: AdminUserSummary | None = None
    payments: list[AdminPaymentRead] = []
    esim_profile: AdminEsimProfileRead | None = None


class AdminStockAlert(BaseModel):
    plan_id: int
    plan_name: str | None = None
    available: int


class AdminInventoryStats(BaseModel):
    totals: dict[str, int]
    low_stock_threshold: int
    low_stock_alerts: list[AdminStockAlert]
