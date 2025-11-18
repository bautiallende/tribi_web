from pydantic import BaseModel, ConfigDict, field_serializer
from decimal import Decimal


class CountryBase(BaseModel):
    iso2: str
    name: str


class CountryRead(CountryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class CarrierBase(BaseModel):
    name: str


class CarrierRead(CarrierBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class PlanBase(BaseModel):
    name: str
    data_gb: Decimal
    duration_days: int
    price_usd: Decimal
    description: str | None = None
    is_unlimited: bool = False

    @field_serializer("data_gb", "price_usd")
    def _serialize_decimal(
        self, value: Decimal
    ) -> float:  # pragma: no cover - pydantic hook
        return float(value)


class PlanRead(PlanBase):
    id: int
    country_id: int
    carrier_id: int
    country: CountryRead | None = None
    carrier: CarrierRead | None = None
    model_config = ConfigDict(from_attributes=True)


class PlanDetail(PlanRead):
    pass
