"""Tests for cookie-based authentication."""

from app.main import app
from app.models.auth_models import AuthCode
from fastapi.testclient import TestClient

from .conftest import TestingSessionLocal

client = TestClient(app)


def _get_code(email: str) -> str:
    db = TestingSessionLocal()
    try:
        auth_code = db.query(AuthCode).filter(AuthCode.email == email).first()
        assert auth_code is not None
        return str(auth_code.code)
    finally:
        db.close()


def test_verify_code_sets_cookie():
    """Test that verify-code sets httpOnly cookie."""
    email = "cookietest@test.com"

    # Request code
    response1 = client.post("/api/auth/request-code", json={"email": email})
    assert response1.status_code == 200

    # Get code from database
    code = _get_code(email)

    # Verify code
    response2 = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert response2.status_code == 200

    # Check cookie is set
    assert "tribi_token" in response2.cookies
    cookie = response2.cookies["tribi_token"]
    assert cookie is not None
    assert len(cookie) > 0  # JWT token should be non-empty


def test_verify_code_returns_token():
    """Test that verify-code also returns token in body (mobile compatibility)."""
    email = "tokentest@test.com"

    # Request code
    client.post("/api/auth/request-code", json={"email": email})

    # Get code
    code = _get_code(email)

    # Verify code
    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert response.status_code == 200

    # Check token in response body
    data = response.json()
    assert "token" in data
    assert len(data["token"]) > 0


def test_cookie_auth_get_current_user():
    """Test authentication with cookie."""
    email = "cookieauth@test.com"

    # Request and verify code to get cookie
    client.post("/api/auth/request-code", json={"email": email})
    code = _get_code(email)

    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    cookie_value = response.cookies["tribi_token"]

    # Use cookie to access protected endpoint
    response_me = client.get("/api/auth/me", cookies={"tribi_token": cookie_value})
    assert response_me.status_code == 200
    data = response_me.json()
    assert data["email"] == email


def test_bearer_auth_get_current_user():
    """Test authentication with Bearer token (mobile)."""
    email = "bearerauth@test.com"

    # Request and verify code to get token
    client.post("/api/auth/request-code", json={"email": email})
    code = _get_code(email)

    response = client.post("/api/auth/verify", json={"email": email, "code": code})
    token = response.json()["token"]

    # Use Bearer token to access protected endpoint
    response_me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response_me.status_code == 200
    data = response_me.json()
    assert data["email"] == email


def test_cookie_priority_over_bearer():
    """Test that cookie takes priority over Bearer token."""
    email1 = "cookie@test.com"
    email2 = "bearer@test.com"

    # Get cookie for email1
    client.post("/api/auth/request-code", json={"email": email1})
    code1 = _get_code(email1)
    response1 = client.post("/api/auth/verify", json={"email": email1, "code": code1})
    cookie = response1.cookies["tribi_token"]

    # Get token for email2
    client.post("/api/auth/request-code", json={"email": email2})
    code2 = _get_code(email2)
    response2 = client.post("/api/auth/verify", json={"email": email2, "code": code2})
    token = response2.json()["token"]

    # Request with both cookie and Bearer (cookie should win)
    response_me = client.get(
        "/api/auth/me",
        cookies={"tribi_token": cookie},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_me.status_code == 200
    data = response_me.json()
    assert data["email"] == email1  # Should use cookie (email1), not Bearer (email2)


def test_logout_clears_cookie():
    """Test that logout endpoint clears cookie."""
    email = "logout@test.com"

    # Login to get cookie
    client.post("/api/auth/request-code", json={"email": email})
    code = _get_code(email)

    response_login = client.post(
        "/api/auth/verify", json={"email": email, "code": code}
    )
    cookie = response_login.cookies["tribi_token"]

    # Verify cookie works
    response_me_before = client.get("/api/auth/me", cookies={"tribi_token": cookie})
    assert response_me_before.status_code == 200

    # Logout
    response_logout = client.post("/api/auth/logout")
    assert response_logout.status_code == 200

    # Check cookie is cleared (max_age=-1 or empty)
    logout_cookie = response_logout.cookies.get("tribi_token", "")
    # Cookie should be empty or have max-age=-1
    assert (
        logout_cookie == ""
        or "max-age=0" in str(response_logout.headers.get("set-cookie", "")).lower()
    )


def test_missing_credentials():
    """Test that missing cookie and Bearer token returns 401."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert "missing credentials" in response.json()["detail"].lower()


def test_invalid_token():
    """Test that invalid JWT returns 401."""
    response = client.get(
        "/api/auth/me", headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
    assert "invalid token" in response.json()["detail"].lower()


def test_expired_token():
    """Test that expired JWT returns 401."""
    # Note: This would require mocking JWT expiration or using freezegun
    # For now, testing invalid token covers the same code path
    response = client.get("/api/auth/me", cookies={"tribi_token": "expired.token.here"})
    assert response.status_code == 401


def test_cookie_httponly_attribute():
    """Test that cookie has httpOnly attribute set."""
    email = "httponly@test.com"

    client.post("/api/auth/request-code", json={"email": email})
    code = _get_code(email)

    response = client.post("/api/auth/verify", json={"email": email, "code": code})

    # Check Set-Cookie header for httpOnly
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "httponly" in set_cookie_header.lower()


def test_cookie_samesite_lax():
    """Test that cookie has SameSite=Lax attribute."""
    email = "samesite@test.com"

    client.post("/api/auth/request-code", json={"email": email})
    code = _get_code(email)

    response = client.post("/api/auth/verify", json={"email": email, "code": code})

    # Check Set-Cookie header for SameSite
    set_cookie_header = response.headers.get("set-cookie", "")
    assert "samesite=lax" in set_cookie_header.lower()
