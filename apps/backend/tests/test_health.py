from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_returns_status_and_request_id():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "x-request-id" in {k.lower() for k in response.headers.keys()}


def test_health_full_includes_components():
    response = client.get("/health/full")
    assert response.status_code == 200
    data = response.json()
    assert data["database"]["status"] in {"ok", "error"}
    assert "jobs" in data
    assert isinstance(data["jobs"].get("enabled"), bool)
