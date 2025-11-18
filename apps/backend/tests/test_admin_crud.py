import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.models import Carrier, Country, Plan, User

from .conftest import TestingSessionLocal


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_seed_data(setup_database):
    """Remove default seed objects so admin tests start with a blank slate."""
    db = TestingSessionLocal()
    try:
        db.query(Plan).delete()
        db.query(Carrier).delete()
        db.query(Country).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def admin_headers(monkeypatch):
    """Mock admin authentication."""
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@tribi.app")
    monkeypatch.setattr(settings, "admin_emails_list", ["admin@tribi.app"])

    # Mock get_current_admin to return admin user
    from app.api.auth import get_current_admin

    def mock_admin():
        return User(id=1, email="admin@tribi.app")

    app.dependency_overrides[get_current_admin] = mock_admin

    return {"Authorization": "Bearer mock-admin-token"}


@pytest.fixture
def non_admin_headers():
    """Mock non-admin authentication."""
    from app.api.auth import get_current_admin

    def mock_non_admin():
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )

    app.dependency_overrides[get_current_admin] = mock_non_admin

    return {"Authorization": "Bearer mock-user-token"}


# ========================================
# Countries CRUD Tests
# ========================================


def test_create_country(client, admin_headers):
    """Test creating a new country."""
    response = client.post(
        "/admin/countries",
        json={"iso2": "US", "name": "United States"},
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["iso2"] == "US"
    assert data["name"] == "United States"
    assert "id" in data


def test_create_country_uppercase_iso2(client, admin_headers):
    """Test ISO2 is automatically uppercased."""
    response = client.post(
        "/admin/countries", json={"iso2": "mx", "name": "Mexico"}, headers=admin_headers
    )
    assert response.status_code == 201
    assert response.json()["iso2"] == "MX"


def test_create_country_duplicate_iso2(client, admin_headers):
    """Test duplicate ISO2 is rejected."""
    client.post(
        "/admin/countries", json={"iso2": "CA", "name": "Canada"}, headers=admin_headers
    )

    response = client.post(
        "/admin/countries",
        json={"iso2": "CA", "name": "Canada Duplicate"},
        headers=admin_headers,
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_country_invalid_iso2(client, admin_headers):
    """Test invalid ISO2 format is rejected."""
    # Too long
    response = client.post(
        "/admin/countries",
        json={"iso2": "USA", "name": "United States"},
        headers=admin_headers,
    )
    assert response.status_code == 400

    # With numbers
    response = client.post(
        "/admin/countries",
        json={"iso2": "U1", "name": "United States"},
        headers=admin_headers,
    )
    assert response.status_code == 400


def test_create_country_non_admin(client, non_admin_headers):
    """Test non-admin cannot create countries."""
    response = client.post(
        "/admin/countries",
        json={"iso2": "FR", "name": "France"},
        headers=non_admin_headers,
    )
    assert response.status_code == 403


def test_list_countries(client, admin_headers):
    """Test listing countries with pagination."""
    # Create test data
    client.post(
        "/admin/countries",
        json={"iso2": "US", "name": "United States"},
        headers=admin_headers,
    )
    client.post(
        "/admin/countries", json={"iso2": "MX", "name": "Mexico"}, headers=admin_headers
    )
    client.post(
        "/admin/countries", json={"iso2": "CA", "name": "Canada"}, headers=admin_headers
    )

    response = client.get("/admin/countries?page=1&page_size=2", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["total_pages"] == 2


def test_list_countries_search(client, admin_headers):
    """Test searching countries."""
    client.post(
        "/admin/countries",
        json={"iso2": "US", "name": "United States"},
        headers=admin_headers,
    )
    client.post(
        "/admin/countries",
        json={"iso2": "GB", "name": "United Kingdom"},
        headers=admin_headers,
    )

    response = client.get("/admin/countries?q=United", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2

    response = client.get("/admin/countries?q=States", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_country(client, admin_headers):
    """Test updating a country."""
    # Create
    create_response = client.post(
        "/admin/countries", json={"iso2": "FR", "name": "France"}, headers=admin_headers
    )
    country_id = create_response.json()["id"]

    # Update
    response = client.put(
        f"/admin/countries/{country_id}",
        json={"name": "French Republic"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "French Republic"
    assert response.json()["iso2"] == "FR"  # Unchanged


def test_update_country_iso2(client, admin_headers):
    """Test updating country ISO2."""
    create_response = client.post(
        "/admin/countries",
        json={"iso2": "UK", "name": "United Kingdom"},
        headers=admin_headers,
    )
    country_id = create_response.json()["id"]

    response = client.put(
        f"/admin/countries/{country_id}", json={"iso2": "GB"}, headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["iso2"] == "GB"


def test_update_country_not_found(client, admin_headers):
    """Test updating non-existent country."""
    response = client.put(
        "/admin/countries/99999", json={"name": "Atlantis"}, headers=admin_headers
    )
    assert response.status_code == 404


def test_delete_country(client, admin_headers):
    """Test deleting a country."""
    create_response = client.post(
        "/admin/countries",
        json={"iso2": "DE", "name": "Germany"},
        headers=admin_headers,
    )
    country_id = create_response.json()["id"]

    response = client.delete(f"/admin/countries/{country_id}", headers=admin_headers)
    assert response.status_code == 204

    # Verify deleted
    get_response = client.get("/admin/countries", headers=admin_headers)
    assert all(c["id"] != country_id for c in get_response.json()["items"])


def test_delete_country_with_plans(client, admin_headers):
    """Test cannot delete country with dependent plans."""
    # Create country and carrier
    country_response = client.post(
        "/admin/countries", json={"iso2": "ES", "name": "Spain"}, headers=admin_headers
    )
    country_id = country_response.json()["id"]

    carrier_response = client.post(
        "/admin/carriers", json={"name": "Vodafone"}, headers=admin_headers
    )
    carrier_id = carrier_response.json()["id"]

    # Create plan
    client.post(
        "/admin/plans",
        json={
            "country_id": country_id,
            "carrier_id": carrier_id,
            "name": "Spain 5GB",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 15.0,
        },
        headers=admin_headers,
    )

    # Try to delete country
    response = client.delete(f"/admin/countries/{country_id}", headers=admin_headers)
    assert response.status_code == 409
    assert "plan(s) reference it" in response.json()["detail"]


# ========================================
# Carriers CRUD Tests
# ========================================


def test_create_carrier(client, admin_headers):
    """Test creating a new carrier."""
    response = client.post(
        "/admin/carriers", json={"name": "AT&T"}, headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AT&T"
    assert "id" in data


def test_create_carrier_empty_name(client, admin_headers):
    """Test carrier name cannot be empty."""
    response = client.post(
        "/admin/carriers", json={"name": "   "}, headers=admin_headers
    )
    assert response.status_code == 400
    assert "cannot be empty" in response.json()["detail"]


def test_create_carrier_duplicate(client, admin_headers):
    """Test duplicate carrier name is rejected."""
    client.post("/admin/carriers", json={"name": "Verizon"}, headers=admin_headers)

    response = client.post(
        "/admin/carriers", json={"name": "Verizon"}, headers=admin_headers
    )
    assert response.status_code == 409


def test_list_carriers(client, admin_headers):
    """Test listing carriers with pagination."""
    client.post("/admin/carriers", json={"name": "T-Mobile"}, headers=admin_headers)
    client.post("/admin/carriers", json={"name": "Sprint"}, headers=admin_headers)

    response = client.get("/admin/carriers?page=1&page_size=10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_carriers_search(client, admin_headers):
    """Test searching carriers."""
    client.post("/admin/carriers", json={"name": "Orange"}, headers=admin_headers)
    client.post("/admin/carriers", json={"name": "T-Mobile"}, headers=admin_headers)

    response = client.get("/admin/carriers?q=Orange", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_carrier(client, admin_headers):
    """Test updating a carrier."""
    create_response = client.post(
        "/admin/carriers", json={"name": "Old Name"}, headers=admin_headers
    )
    carrier_id = create_response.json()["id"]

    response = client.put(
        f"/admin/carriers/{carrier_id}",
        json={"name": "New Name"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


def test_delete_carrier(client, admin_headers):
    """Test deleting a carrier."""
    create_response = client.post(
        "/admin/carriers", json={"name": "Temporary Carrier"}, headers=admin_headers
    )
    carrier_id = create_response.json()["id"]

    response = client.delete(f"/admin/carriers/{carrier_id}", headers=admin_headers)
    assert response.status_code == 204


def test_delete_carrier_with_plans(client, admin_headers):
    """Test cannot delete carrier with dependent plans."""
    # Create country and carrier
    country_response = client.post(
        "/admin/countries", json={"iso2": "IT", "name": "Italy"}, headers=admin_headers
    )
    country_id = country_response.json()["id"]

    carrier_response = client.post(
        "/admin/carriers", json={"name": "TIM"}, headers=admin_headers
    )
    carrier_id = carrier_response.json()["id"]

    # Create plan
    client.post(
        "/admin/plans",
        json={
            "country_id": country_id,
            "carrier_id": carrier_id,
            "name": "Italy 3GB",
            "data_gb": 3.0,
            "duration_days": 5,
            "price_usd": 10.0,
        },
        headers=admin_headers,
    )

    # Try to delete carrier
    response = client.delete(f"/admin/carriers/{carrier_id}", headers=admin_headers)
    assert response.status_code == 409


# ========================================
# Plans CRUD Tests
# ========================================


def test_create_plan(client, admin_headers):
    """Test creating a new plan."""
    # Create dependencies
    country_response = client.post(
        "/admin/countries", json={"iso2": "JP", "name": "Japan"}, headers=admin_headers
    )
    country_id = country_response.json()["id"]

    carrier_response = client.post(
        "/admin/carriers", json={"name": "NTT Docomo"}, headers=admin_headers
    )
    carrier_id = carrier_response.json()["id"]

    # Create plan
    response = client.post(
        "/admin/plans",
        json={
            "country_id": country_id,
            "carrier_id": carrier_id,
            "name": "Japan 10GB",
            "data_gb": 10.0,
            "duration_days": 30,
            "price_usd": 25.50,
            "description": "Best plan for Japan",
            "is_unlimited": False,
        },
        headers=admin_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Japan 10GB"
    assert data["data_gb"] == 10.0
    assert data["price_usd"] == 25.50


def test_create_plan_invalid_price(client, admin_headers):
    """Test plan with negative price is rejected."""
    country_response = client.post(
        "/admin/countries", json={"iso2": "BR", "name": "Brazil"}, headers=admin_headers
    )
    carrier_response = client.post(
        "/admin/carriers", json={"name": "Claro"}, headers=admin_headers
    )

    response = client.post(
        "/admin/plans",
        json={
            "country_id": country_response.json()["id"],
            "carrier_id": carrier_response.json()["id"],
            "name": "Invalid Plan",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": -10.0,  # Negative price
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "non-negative" in response.json()["detail"]


def test_create_plan_invalid_duration(client, admin_headers):
    """Test plan with zero or negative duration is rejected."""
    country_response = client.post(
        "/admin/countries",
        json={"iso2": "AR", "name": "Argentina"},
        headers=admin_headers,
    )
    carrier_response = client.post(
        "/admin/carriers", json={"name": "Movistar"}, headers=admin_headers
    )

    response = client.post(
        "/admin/plans",
        json={
            "country_id": country_response.json()["id"],
            "carrier_id": carrier_response.json()["id"],
            "name": "Invalid Plan",
            "data_gb": 5.0,
            "duration_days": 0,  # Zero duration
            "price_usd": 10.0,
        },
        headers=admin_headers,
    )
    assert response.status_code == 400
    assert "positive" in response.json()["detail"]


def test_create_plan_nonexistent_country(client, admin_headers):
    """Test plan with non-existent country is rejected."""
    carrier_response = client.post(
        "/admin/carriers", json={"name": "Test Carrier"}, headers=admin_headers
    )

    response = client.post(
        "/admin/plans",
        json={
            "country_id": 99999,  # Non-existent
            "carrier_id": carrier_response.json()["id"],
            "name": "Invalid Plan",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 10.0,
        },
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert "Country" in response.json()["detail"]


def test_create_plan_nonexistent_carrier(client, admin_headers):
    """Test plan with non-existent carrier is rejected."""
    country_response = client.post(
        "/admin/countries", json={"iso2": "CL", "name": "Chile"}, headers=admin_headers
    )

    response = client.post(
        "/admin/plans",
        json={
            "country_id": country_response.json()["id"],
            "carrier_id": 99999,  # Non-existent
            "name": "Invalid Plan",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 10.0,
        },
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert "Carrier" in response.json()["detail"]


def test_list_plans(client, admin_headers):
    """Test listing plans with pagination."""
    # Create dependencies
    country_response = client.post(
        "/admin/countries",
        json={"iso2": "AU", "name": "Australia"},
        headers=admin_headers,
    )
    carrier_response = client.post(
        "/admin/carriers", json={"name": "Telstra"}, headers=admin_headers
    )

    country_id = country_response.json()["id"]
    carrier_id = carrier_response.json()["id"]

    # Create plans
    for i in range(3):
        client.post(
            "/admin/plans",
            json={
                "country_id": country_id,
                "carrier_id": carrier_id,
                "name": f"Plan {i}",
                "data_gb": float(i + 1),
                "duration_days": 7,
                "price_usd": float(10 + i),
            },
            headers=admin_headers,
        )

    response = client.get("/admin/plans?page=1&page_size=10", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


def test_list_plans_filter_country(client, admin_headers):
    """Test filtering plans by country."""
    # Create two countries
    country1 = client.post(
        "/admin/countries",
        json={"iso2": "NZ", "name": "New Zealand"},
        headers=admin_headers,
    ).json()
    country2 = client.post(
        "/admin/countries",
        json={"iso2": "FI", "name": "Finland"},
        headers=admin_headers,
    ).json()

    carrier = client.post(
        "/admin/carriers", json={"name": "Carrier"}, headers=admin_headers
    ).json()

    # Create plans for each country
    client.post(
        "/admin/plans",
        json={
            "country_id": country1["id"],
            "carrier_id": carrier["id"],
            "name": "NZ Plan",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 15.0,
        },
        headers=admin_headers,
    )
    client.post(
        "/admin/plans",
        json={
            "country_id": country2["id"],
            "carrier_id": carrier["id"],
            "name": "FI Plan",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 15.0,
        },
        headers=admin_headers,
    )

    response = client.get(
        f"/admin/plans?country_id={country1['id']}", headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_update_plan(client, admin_headers):
    """Test updating a plan."""
    # Create plan
    country = client.post(
        "/admin/countries", json={"iso2": "SE", "name": "Sweden"}, headers=admin_headers
    ).json()
    carrier = client.post(
        "/admin/carriers", json={"name": "Telia"}, headers=admin_headers
    ).json()

    plan = client.post(
        "/admin/plans",
        json={
            "country_id": country["id"],
            "carrier_id": carrier["id"],
            "name": "Old Name",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 10.0,
        },
        headers=admin_headers,
    ).json()

    # Update
    response = client.put(
        f"/admin/plans/{plan['id']}",
        json={"name": "New Name", "price_usd": 12.0},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"
    assert response.json()["price_usd"] == 12.0


def test_delete_plan(client, admin_headers):
    """Test deleting a plan."""
    # Create plan
    country = client.post(
        "/admin/countries", json={"iso2": "NO", "name": "Norway"}, headers=admin_headers
    ).json()
    carrier = client.post(
        "/admin/carriers", json={"name": "Telenor"}, headers=admin_headers
    ).json()

    plan = client.post(
        "/admin/plans",
        json={
            "country_id": country["id"],
            "carrier_id": carrier["id"],
            "name": "Temp Plan",
            "data_gb": 5.0,
            "duration_days": 7,
            "price_usd": 10.0,
        },
        headers=admin_headers,
    ).json()

    response = client.delete(f"/admin/plans/{plan['id']}", headers=admin_headers)
    assert response.status_code == 204
