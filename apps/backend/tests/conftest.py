"""Pytest configuration and fixtures."""

from decimal import Decimal

import pytest
from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models import Base, Carrier, Country, Plan, User
from fastapi.testclient import TestClient
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


@pytest.fixture
def client():
    """FastAPI test client shared across backend tests."""
    return TestClient(app)


@pytest.fixture
def admin_headers(monkeypatch):
    """Mock admin authentication header for admin-only endpoints."""
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@tribi.app")
    monkeypatch.setattr(settings, "admin_emails_list", ["admin@tribi.app"])

    from app.api.auth import get_current_admin

    def mock_admin():
        return User(id=1, email="admin@tribi.app")

    app.dependency_overrides[get_current_admin] = mock_admin

    return {"Authorization": "Bearer mock-admin-token"}


@pytest.fixture
def non_admin_headers():
    """Headers that simulate a forbidden admin request."""

    from app.api.auth import get_current_admin
    from fastapi import HTTPException, status

    def mock_non_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    app.dependency_overrides[get_current_admin] = mock_non_admin

    return {"Authorization": "Bearer mock-user-token"}


@pytest.fixture
def cleanup_seed_data(request):
    """Remove default seed objects so admin-focused tests start clean."""
    request.getfixturevalue("setup_database")
    db = TestingSessionLocal()
    try:
        db.query(Plan).delete()
        db.query(Carrier).delete()
        db.query(Country).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def db_session(request):
    """Provide a database session for inserting test records."""
    request.getfixturevalue("setup_database")
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    finally:
        session.close()
