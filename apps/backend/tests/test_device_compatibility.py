from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_device_compatibility_likely_compatible_iphone():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1 iPhone 14"
    response = client.get("/api/device/compatibility", params={"user_agent": ua})
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "likely_compatible"
    assert "iPhone" in data["message"]


def test_device_compatibility_likely_incompatible_old_iphone():
    ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1 iPhone 6"
    response = client.get("/api/device/compatibility", params={"user_agent": ua})
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "likely_incompatible"


def test_device_compatibility_android_unknown():
    ua = "Mozilla/5.0 (Linux; Android 11; SM-G960U Build/RP1A.200720.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.5481.65 Mobile Safari/537.36"
    response = client.get("/api/device/compatibility", params={"user_agent": ua})
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] in {"unknown", "likely_incompatible", "likely_compatible"}
    assert data["user_agent"] == ua


def test_device_compatibility_missing_ua_returns_error():
    response = client.get("/api/device/compatibility", params={"user_agent": ""})
    assert response.status_code == 422
