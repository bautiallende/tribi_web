"""Tests for auth endpoints."""

from unittest.mock import patch

from app.main import app
from app.models import AuthCode, User
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


@patch("app.api.auth.send_email_smtp")
def test_request_code_creates_user(mock_email):
    """Test requesting an OTP code for a new email."""
    mock_email.return_value = None

    response = client.post("/api/auth/request-code", json={"email": "new@example.com"})
    assert response.status_code == 200
    assert response.json() == {"message": "code_sent"}

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "new@example.com").first()
        assert user is not None
    finally:
        db.close()


@patch("app.api.auth.send_email_smtp")
def test_verify_code_success(mock_email):
    """Test verifying an OTP code successfully."""
    mock_email.return_value = None

    # Request code
    client.post("/api/auth/request-code", json={"email": "verify@test.com"})

    # Get code from DB
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "verify@test.com").first()
        assert user is not None
        auth_code = db.query(AuthCode).filter(AuthCode.user_id == user.id).first()
        assert auth_code is not None
        code = str(auth_code.code)
    finally:
        db.close()

    # Verify code
    response = client.post(
        "/api/auth/verify", json={"email": "verify@test.com", "code": code}
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "verify@test.com"


def test_verify_code_invalid():
    """Test verifying with an invalid code."""
    response = client.post(
        "/api/auth/verify", json={"email": "nouser@test.com", "code": "999999"}
    )
    assert response.status_code == 404


@patch("app.api.auth.send_email_smtp")
def test_get_me_success(mock_email):
    """Test getting user profile with valid token."""
    mock_email.return_value = None

    # Request and verify code
    client.post("/api/auth/request-code", json={"email": "me@test.com"})

    code = _get_code("me@test.com")

    verify_response = client.post(
        "/api/auth/verify", json={"email": "me@test.com", "code": code}
    )
    token = verify_response.json()["token"]

    # Get profile
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"


def test_get_me_no_token():
    """Test get me without token."""
    client.cookies.clear()
    response = client.get("/api/auth/me")
    assert response.status_code == 401
