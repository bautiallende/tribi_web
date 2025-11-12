from pydantic import BaseModel, Field
from typing import Generic, TypeVar


# ========================================
# Country Schemas
# ========================================

class CountryCreate(BaseModel):
    iso2: str = Field(..., min_length=2, max_length=2, description="Two-letter country code")
    name: str = Field(..., min_length=1, max_length=255, description="Country name")


class CountryUpdate(BaseModel):
    iso2: str | None = Field(None, min_length=2, max_length=2, description="Two-letter country code")
    name: str | None = Field(None, min_length=1, max_length=255, description="Country name")


# ========================================
# Carrier Schemas
# ========================================

class CarrierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Carrier name")


class CarrierUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255, description="Carrier name")


# ========================================
# Plan Schemas
# ========================================

class PlanCreate(BaseModel):
    country_id: int = Field(..., gt=0, description="Country ID")
    carrier_id: int = Field(..., gt=0, description="Carrier ID")
    name: str = Field(..., min_length=1, max_length=255, description="Plan name")
    data_gb: float = Field(..., ge=0, description="Data in GB")
    duration_days: int = Field(..., gt=0, description="Duration in days")
    price_usd: float = Field(..., ge=0, description="Price in USD")
    description: str | None = Field(None, description="Plan description")
    is_unlimited: bool = Field(False, description="Is unlimited data")


class PlanUpdate(BaseModel):
    country_id: int | None = Field(None, gt=0, description="Country ID")
    carrier_id: int | None = Field(None, gt=0, description="Carrier ID")
    name: str | None = Field(None, min_length=1, max_length=255, description="Plan name")
    data_gb: float | None = Field(None, ge=0, description="Data in GB")
    duration_days: int | None = Field(None, gt=0, description="Duration in days")
    price_usd: float | None = Field(None, ge=0, description="Price in USD")
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
