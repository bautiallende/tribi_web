"""Pytest configuration and fixtures."""

from decimal import Decimal

import pytest
from app.db.session import get_db
from app.main import app
from app.models import Base, Carrier, Country, Plan
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Use SQLite in-memory database for tests with a shared engine
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Reset database schema before each test and clean up overrides afterwards."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        if not db.query(Plan).filter(Plan.id == 1).first():
            country = Country(id=1, iso2="US", name="United States")
            carrier = Carrier(id=1, name="Tribi Test Carrier")
            plan = Plan(
                id=1,
                country=country,
                carrier=carrier,
                name="Starter 10GB / 30 Days",
                data_gb=Decimal("10"),
                duration_days=30,
                price_usd=Decimal("99.00"),
                description="Seed plan for tests",
                is_unlimited=False,
            )
            db.add_all([country, carrier, plan])
            db.commit()
    finally:
        db.close()

    app.dependency_overrides[get_db] = _override_get_db

    yield

    app.dependency_overrides.clear()
