import pytest
from app.api.auth import get_current_admin
from app.core.config import settings
from app.models import User
from fastapi import HTTPException


def test_get_current_admin_with_admin_user(monkeypatch):
    """Test get_current_admin allows access for admin users."""
    # Mock admin emails
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@tribi.app,superuser@tribi.app")
    monkeypatch.setattr(
        settings, "admin_emails_list", ["admin@tribi.app", "superuser@tribi.app"]
    )

    # Create mock admin user
    admin_user = User(id=1, email="admin@tribi.app")

    # Should not raise exception
    result = get_current_admin(current_user=admin_user)
    assert result == admin_user


def test_get_current_admin_case_insensitive(monkeypatch):
    """Test get_current_admin is case-insensitive."""
    # Mock admin emails (lowercase)
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@tribi.app")
    monkeypatch.setattr(settings, "admin_emails_list", ["admin@tribi.app"])

    # Create mock user with uppercase email
    admin_user = User(id=1, email="ADMIN@tribi.app")

    # Should not raise exception
    result = get_current_admin(current_user=admin_user)
    assert result == admin_user


def test_get_current_admin_with_non_admin_user(monkeypatch):
    """Test get_current_admin blocks non-admin users with 403."""
    # Mock admin emails
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "admin@tribi.app")
    monkeypatch.setattr(settings, "admin_emails_list", ["admin@tribi.app"])

    # Create mock non-admin user
    regular_user = User(id=2, email="user@example.com")

    # Should raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin(current_user=regular_user)

    assert exc_info.value.status_code == 403
    assert "Admin access required" in exc_info.value.detail


def test_get_current_admin_with_empty_admin_list(monkeypatch):
    """Test get_current_admin blocks all users when no admins configured."""
    # Mock empty admin list
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "")
    monkeypatch.setattr(settings, "admin_emails_list", [])

    # Create mock user
    user = User(id=1, email="admin@tribi.app")

    # Should raise 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        get_current_admin(current_user=user)

    assert exc_info.value.status_code == 403


def test_get_current_admin_with_multiple_admins(monkeypatch):
    """Test get_current_admin allows multiple admin emails."""
    # Mock multiple admin emails
    monkeypatch.setattr(
        settings, "ADMIN_EMAILS", "admin1@tribi.app,admin2@tribi.app,admin3@tribi.app"
    )
    monkeypatch.setattr(
        settings,
        "admin_emails_list",
        ["admin1@tribi.app", "admin2@tribi.app", "admin3@tribi.app"],
    )

    # Test each admin
    admin1 = User(id=1, email="admin1@tribi.app")
    admin2 = User(id=2, email="admin2@tribi.app")
    admin3 = User(id=3, email="admin3@tribi.app")

    assert get_current_admin(current_user=admin1) == admin1
    assert get_current_admin(current_user=admin2) == admin2
    assert get_current_admin(current_user=admin3) == admin3
