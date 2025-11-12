from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Country(Base):
    __tablename__ = "countries"

    id = Column(Integer, primary_key=True, index=True)
    iso2 = Column(String(2), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)

    plans = relationship("Plan", back_populates="country")

    __table_args__ = (
        Index("idx_country_iso2_name", "iso2", "name"),
    )


class Carrier(Base):
    __tablename__ = "carriers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)

    plans = relationship("Plan", back_populates="carrier")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=False, index=True)
    carrier_id = Column(Integer, ForeignKey("carriers.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    data_gb = Column(Numeric(5, 2), nullable=False)
    duration_days = Column(Integer, nullable=False)
    price_usd = Column(Numeric(8, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_unlimited = Column(Boolean, default=False)

    country = relationship("Country", back_populates="plans")
    carrier = relationship("Carrier", back_populates="plans")

    __table_args__ = (
        Index("idx_plan_country_carrier", "country_id", "carrier_id"),
        Index("idx_plan_price", "price_usd"),
    )
