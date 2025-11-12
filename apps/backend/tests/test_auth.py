"""Tests for auth endpoints."""
import tempfile
import os
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.models import Base, User, AuthCode
from app.db.session import get_db

# Create a temporary SQLite database file for testing
temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
temp_db_path = temp_db.name
temp_db.close()

engine = create_engine(f"sqlite:///{temp_db_path}")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@patch("app.api.auth.send_email_smtp")
def test_request_code_creates_user(mock_email):
    """Test requesting an OTP code for a new email."""
    mock_email.return_value = None
    
    response = client.post("/auth/request-code", json={"email": "new@example.com"})
    assert response.status_code == 200
    assert response.json() == {"message": "code_sent"}

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "new@example.com").first()
    assert user is not None
    db.close()


@patch("app.api.auth.send_email_smtp")
def test_verify_code_success(mock_email):
    """Test verifying an OTP code successfully."""
    mock_email.return_value = None
    
    # Request code
    client.post("/auth/request-code", json={"email": "verify@test.com"})

    # Get code from DB
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "verify@test.com").first()
    auth_code = db.query(AuthCode).filter(AuthCode.user_id == user.id).first()
    code = auth_code.code
    db.close()

    # Verify code
    response = client.post("/auth/verify", json={"email": "verify@test.com", "code": code})
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["user"]["email"] == "verify@test.com"


def test_verify_code_invalid():
    """Test verifying with an invalid code."""
    response = client.post("/auth/verify", json={"email": "nouser@test.com", "code": "999999"})
    assert response.status_code == 404


@patch("app.api.auth.send_email_smtp")
def test_get_me_success(mock_email):
    """Test getting user profile with valid token."""
    mock_email.return_value = None
    
    # Request and verify code
    client.post("/auth/request-code", json={"email": "me@test.com"})

    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == "me@test.com").first()
    auth_code = db.query(AuthCode).filter(AuthCode.user_id == user.id).first()
    code = auth_code.code
    db.close()

    verify_response = client.post("/auth/verify", json={"email": "me@test.com", "code": code})
    token = verify_response.json()["token"]

    # Get profile
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "me@test.com"


def test_get_me_no_token():
    """Test get me without token."""
    response = client.get("/auth/me")
    assert response.status_code == 401


# Clean up temp DB after all tests
def teardown_module():
    """Clean up temp database."""
    try:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)
    except Exception:
        pass  # Ignore cleanup errors
