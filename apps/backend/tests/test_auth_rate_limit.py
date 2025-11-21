"""Tests for authentication rate limiting."""

from datetime import datetime, timedelta

from app.core.config import settings
from app.main import app
from app.models.auth_models import AuthCode
from fastapi.testclient import TestClient
from freezegun import freeze_time

from .conftest import TestingSessionLocal

client = TestClient(app)


def test_rate_limit_60_seconds():
    """Test 1 code per 60 seconds rate limit."""
    email = "ratelimit60@test.com"

    # First request should succeed
    response1 = client.post("/api/auth/request-code", json={"email": email})
    assert response1.status_code == 200

    # Second request within 60s should fail
    response2 = client.post("/api/auth/request-code", json={"email": email})
    assert response2.status_code == 429
    assert "wait 60s" in response2.json()["detail"].lower()


def test_rate_limit_60_seconds_expires():
    """Test rate limit resets after 60 seconds."""
    email = "ratelimit60expire@test.com"

    # First request at T=0
    with freeze_time("2024-01-01 12:00:00"):
        response1 = client.post("/api/auth/request-code", json={"email": email})
        assert response1.status_code == 200

    # Request at T=59s should fail
    with freeze_time("2024-01-01 12:00:59"):
        response2 = client.post("/api/auth/request-code", json={"email": email})
        assert response2.status_code == 429

    # Request at T=61s should succeed
    with freeze_time("2024-01-01 12:01:01"):
        response3 = client.post("/api/auth/request-code", json={"email": email})
        assert response3.status_code == 200


def test_rate_limit_24_hours():
    """Test 5 codes per 24 hours rate limit."""
    email = "ratelimit24h@test.com"

    # Send 5 codes successfully (61s apart each)
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(5):
        with freeze_time(base_time + timedelta(seconds=61 * i)):
            response = client.post("/api/auth/request-code", json={"email": email})
            assert response.status_code == 200, f"Request {i+1} failed"

    # 6th request within 24h should fail
    with freeze_time(base_time + timedelta(seconds=61 * 5)):
        response6 = client.post("/api/auth/request-code", json={"email": email})
        assert response6.status_code == 429
        assert "24h" in response6.json()["detail"].lower()


def test_rate_limit_24_hours_expires():
    """Test 24h rate limit resets after 24 hours."""
    email = "ratelimit24hexpire@test.com"

    # Send 5 codes at T=0
    base_time = datetime(2024, 1, 1, 12, 0, 0)
    for i in range(5):
        with freeze_time(base_time + timedelta(seconds=61 * i)):
            response = client.post("/api/auth/request-code", json={"email": email})
            assert response.status_code == 200

    # 6th request at T=23h should fail
    with freeze_time(base_time + timedelta(hours=23)):
        response6 = client.post("/api/auth/request-code", json={"email": email})
        assert response6.status_code == 429

    # Request at T=24h+1s should succeed (oldest code expired)
    with freeze_time(base_time + timedelta(hours=24, seconds=1)):
        response7 = client.post("/api/auth/request-code", json={"email": email})
        assert response7.status_code == 200


def test_rate_limit_different_ips():
    """Test rate limiting is per email+IP (different IPs allowed)."""
    email = "ratelimitip@test.com"

    # First request from IP1
    response1 = client.post(
        "/api/auth/request-code",
        json={"email": email},
        headers={"X-Forwarded-For": "192.168.1.1"},
    )
    assert response1.status_code == 200

    # Second request from IP2 (different IP) should succeed
    response2 = client.post(
        "/api/auth/request-code",
        json={"email": email},
        headers={"X-Forwarded-For": "192.168.1.2"},
    )
    assert response2.status_code == 200


def test_rate_limit_same_ip():
    """Test rate limiting enforces same email+IP combination."""
    email = "ratelimitsameip@test.com"
    ip = "192.168.1.100"

    # First request
    response1 = client.post(
        "/api/auth/request-code", json={"email": email}, headers={"X-Forwarded-For": ip}
    )
    assert response1.status_code == 200

    # Second request from same IP should fail
    response2 = client.post(
        "/api/auth/request-code", json={"email": email}, headers={"X-Forwarded-For": ip}
    )
    assert response2.status_code == 429


def test_rate_limit_different_emails():
    """Test rate limiting is per email (different emails allowed)."""
    ip = "192.168.1.200"

    # First request for email1
    response1 = client.post(
        "/api/auth/request-code",
        json={"email": "user1@test.com"},
        headers={"X-Forwarded-For": ip},
    )
    assert response1.status_code == 200

    # Second request for email2 (same IP) should succeed
    response2 = client.post(
        "/api/auth/request-code",
        json={"email": "user2@test.com"},
        headers={"X-Forwarded-For": ip},
    )
    assert response2.status_code == 200


def test_rate_limit_ip_from_header():
    """Test IP extraction from X-Forwarded-For header."""
    email = "ipheader@test.com"

    # Request with X-Forwarded-For
    response1 = client.post(
        "/api/auth/request-code",
        json={"email": email},
        headers={"X-Forwarded-For": "10.0.0.1, 192.168.1.1"},  # Proxy chain
    )
    assert response1.status_code == 200

    # Verify IP was stored correctly (should use first IP in chain)
    db = TestingSessionLocal()
    auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
    assert auth_code.ip_address == "10.0.0.1"
    db.close()


def test_rate_limit_attempts_tracked():
    """Test that attempts are tracked in AuthCode."""
    email = "attempts@test.com"

    # First request
    response = client.post("/api/auth/request-code", json={"email": email})
    assert response.status_code == 200

    # Verify attempts initialized to 0
    db = TestingSessionLocal()
    auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
    assert auth_code.attempts == 0
    db.close()


def test_rate_limit_created_at_indexed():
    """Test that created_at is stored for time-window queries."""
    email = "createdat@test.com"

    with freeze_time("2024-01-01 12:00:00"):
        response = client.post("/api/auth/request-code", json={"email": email})
        assert response.status_code == 200

    # Verify created_at was stored
    db = TestingSessionLocal()
    auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
    assert auth_code.created_at is not None
    assert auth_code.created_at.year == 2024
    assert auth_code.created_at.month == 1
    assert auth_code.created_at.day == 1
    db.close()


def test_rate_limit_ip_daily_cap(monkeypatch):
    """Test IP-based quota limits total codes per 24h window."""
    ip = "203.0.113.50"
    emails = [f"ipcap{i}@test.com" for i in range(3)]

    monkeypatch.setattr(settings, "RATE_LIMIT_CODES_PER_IP_PER_DAY", 2)

    for email in emails[:2]:
        response = client.post(
            "/api/auth/request-code",
            json={"email": email},
            headers={"X-Forwarded-For": ip},
        )
        assert response.status_code == 200, f"Expected success for {email}"

    blocked = client.post(
        "/api/auth/request-code",
        json={"email": emails[2]},
        headers={"X-Forwarded-For": ip},
    )
    assert blocked.status_code == 429
    assert "too many codes" in blocked.json()["detail"].lower()
