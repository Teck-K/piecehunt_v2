"""Unit tests for UserHandler (v2.0.0 - API-based).

Tests the UserHandler in the context of the PieceHunt API-based architecture.
All database operations now go through the HTTP API, not a local database.

Test coverage:
    - reauthenticate: successful login, wrong password, API error handling
    - refresh_session: token refresh, error handling, email preservation
    - delete_account: successful deletion, wrong password, not logged in
    - check_password_requirements: validation rules
    - check_email: format validation
    - auth_session management: set, clear, property access

Note: These tests mock the API layer (services.api_client) to avoid requiring
a live PieceHunt API server.
"""

from unittest.mock import patch

import pytest

from backend.handlers.user_handler import UserHandler
from backend.helper.singletonmeta import SingletonMeta
from services.api_client import ApiError


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the UserHandler singleton before and after every test.

    UserHandler uses SingletonMeta, so without this fixture state from one
    test would leak into the next.
    """
    SingletonMeta._instances.pop(UserHandler, None)
    yield
    SingletonMeta._instances.pop(UserHandler, None)


@pytest.fixture
def user_handler():
    """Return a fresh UserHandler instance."""
    return UserHandler()


# ── Reauthenticate ────────────────────────────────────────────────────────────


class TestReauthenticate:
    """Tests for UserHandler.reauthenticate() - API-based login via email/password."""

    @patch("backend.handlers.user_handler.api_login")
    def test_successful_reauthentication(self, mock_api_login, user_handler):
        """Should return an AuthSession when API returns valid credentials."""
        mock_api_login.return_value = {
            "user_id": "user-123",
            "access_token": "access-token-abc",
            "refresh_token": "refresh-token-xyz",
            "email": "user@example.com",
        }

        session = user_handler.reauthenticate("user@example.com", "password123")

        assert session is not None
        assert session.user_id == "user-123"
        assert session.access_token == "access-token-abc"
        assert session.refresh_token == "refresh-token-xyz"
        assert session.email == "user@example.com"
        mock_api_login.assert_called_once_with("user@example.com", "password123")

    @patch("backend.handlers.user_handler.api_login")
    def test_reauthenticate_wrong_password(self, mock_api_login, user_handler):
        """Should return None when API raises ApiError (wrong password)."""
        mock_api_login.side_effect = ApiError("Unauthorized", status_code=401)

        session = user_handler.reauthenticate("user@example.com", "wrongpassword")

        assert session is None
        mock_api_login.assert_called_once()

    @patch("backend.handlers.user_handler.api_login")
    def test_reauthenticate_api_error(self, mock_api_login, user_handler):
        """Should return None when API is unreachable."""
        mock_api_login.side_effect = ApiError("Connection failed", status_code=None)

        session = user_handler.reauthenticate("user@example.com", "password123")

        assert session is None


# ── Refresh Session ───────────────────────────────────────────────────────────


class TestRefreshSession:
    """Tests for UserHandler.refresh_session() - token refresh via API."""

    @patch("backend.handlers.user_handler.api_refresh_auth_token")
    def test_successful_token_refresh(self, mock_api_refresh, user_handler):
        """Should update the auth session with new tokens."""
        # Set up initial session
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="old-token",
            refresh_token="refresh-xyz",
            email="user@example.com",
        )

        # Mock API response with new tokens
        mock_api_refresh.return_value = {
            "user_id": "user-123",
            "access_token": "new-token",
            "refresh_token": "new-refresh",
        }

        user_handler.refresh_session()

        # Verify session was updated
        assert user_handler.auth_session.access_token == "new-token"
        assert user_handler.auth_session.refresh_token == "new-refresh"
        # Email should be preserved from old session
        assert user_handler.auth_session.email == "user@example.com"
        mock_api_refresh.assert_called_once_with("refresh-xyz")

    def test_refresh_session_without_login(self, user_handler):
        """Should raise RuntimeError when no session exists."""
        with pytest.raises(RuntimeError, match="No session to refresh"):
            user_handler.refresh_session()

    @patch("backend.handlers.user_handler.api_refresh_auth_token")
    def test_refresh_session_api_error(self, mock_api_refresh, user_handler):
        """Should re-raise ApiError if refresh token is invalid."""
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="old-token",
            refresh_token="invalid-token",
            email="user@example.com",
        )

        mock_api_refresh.side_effect = ApiError("Refresh token expired", status_code=401)

        with pytest.raises(ApiError):
            user_handler.refresh_session()


# ── Delete Account ────────────────────────────────────────────────────────────


class TestDeleteAccount:
    """Tests for UserHandler.delete_account() - account deletion."""

    @patch("backend.handlers.user_handler.request_account_deletion")
    @patch("backend.handlers.user_handler.api_login")
    def test_successful_account_deletion(self, mock_api_login, mock_delete, user_handler):
        """Should delete account and clear session on success."""
        # Set up logged-in session
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="token-abc",
            refresh_token="refresh-xyz",
            email="user@example.com",
        )

        # Mock re-authentication
        mock_api_login.return_value = {
            "user_id": "user-123",
            "access_token": "token-abc",
            "refresh_token": "refresh-xyz",
            "email": "user@example.com",
        }

        # Mock successful deletion
        mock_delete.return_value = {}

        success, msg = user_handler.delete_account("correct-password")

        assert success is True
        assert "successfully" in msg.lower()
        assert user_handler.auth_session is None
        mock_api_login.assert_called_once_with("user@example.com", "correct-password")
        mock_delete.assert_called_once_with("token-abc")

    def test_delete_account_not_logged_in(self, user_handler):
        """Should return False when no session exists."""
        success, msg = user_handler.delete_account("password123")

        assert success is False
        assert "not logged in" in msg.lower()

    @patch("backend.handlers.user_handler.api_login")
    def test_delete_account_wrong_password(self, mock_api_login, user_handler):
        """Should return False when password is incorrect."""
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="token-abc",
            refresh_token="refresh-xyz",
            email="user@example.com",
        )

        mock_api_login.side_effect = ApiError("Unauthorized", status_code=401)

        success, msg = user_handler.delete_account("wrong-password")

        assert success is False
        assert "incorrect password" in msg.lower()

    @patch("backend.handlers.user_handler.request_account_deletion")
    @patch("backend.handlers.user_handler.api_login")
    def test_delete_account_api_error(self, mock_api_login, mock_delete, user_handler):
        """Should return False when deletion API call fails."""
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="token-abc",
            refresh_token="refresh-xyz",
            email="user@example.com",
        )

        mock_api_login.return_value = {
            "user_id": "user-123",
            "access_token": "token-abc",
            "refresh_token": "refresh-xyz",
            "email": "user@example.com",
        }

        mock_delete.side_effect = ApiError("Server error", status_code=500)

        success, msg = user_handler.delete_account("password123")

        assert success is False


# ── Password Requirements ─────────────────────────────────────────────────────


class TestPasswordRequirements:
    """Tests for UserHandler.check_password_requirements() validation."""

    def test_valid_password(self, user_handler):
        """Should accept a valid password."""
        valid, msg = user_handler.check_password_requirements("Password123")

        assert valid is True
        assert msg == ""

    def test_password_too_short(self, user_handler):
        """Should reject password shorter than 6 characters."""
        valid, msg = user_handler.check_password_requirements("Pass1")

        assert valid is False
        assert "too short" in msg.lower()

    def test_password_too_long(self, user_handler):
        """Should reject password longer than 50 characters."""
        long_pass = "a" * 41 + "1bcdefghij"  # 51 characters
        valid, msg = user_handler.check_password_requirements(long_pass)

        assert valid is False
        assert "too long" in msg.lower()

    def test_password_missing_letter(self, user_handler):
        """Should reject password without letters."""
        valid, msg = user_handler.check_password_requirements("123456")

        assert valid is False
        assert "letter" in msg.lower()

    def test_password_missing_digit(self, user_handler):
        """Should reject password without digits."""
        valid, msg = user_handler.check_password_requirements("Password")

        assert valid is False
        assert "number" in msg.lower()

    def test_password_with_spaces(self, user_handler):
        """Should reject password containing spaces."""
        valid, msg = user_handler.check_password_requirements("Pass word 123")

        assert valid is False
        assert "space" in msg.lower()


# ── Email Validation ──────────────────────────────────────────────────────────


class TestEmailValidation:
    """Tests for UserHandler.check_email() validation."""

    def test_valid_email(self, user_handler):
        """Should accept a valid email format."""
        valid, msg = user_handler.check_email("user@example.com")

        assert valid is True
        assert msg == ""

    def test_invalid_email_no_at(self, user_handler):
        """Should reject email without @ symbol."""
        valid, msg = user_handler.check_email("userexample.com")

        assert valid is False
        assert "invalid" in msg.lower()

    def test_invalid_email_no_domain(self, user_handler):
        """Should reject email without domain."""
        valid, msg = user_handler.check_email("user@")

        assert valid is False
        assert "invalid" in msg.lower()

    def test_email_too_long(self, user_handler):
        """Should reject email longer than 254 characters."""
        long_email = "a" * 250 + "@example.com"
        valid, msg = user_handler.check_email(long_email)

        assert valid is False
        assert "maximum" in msg.lower() or "too long" in msg.lower()


# ── Auth Session Management ───────────────────────────────────────────────────


class TestAuthSessionManagement:
    """Tests for UserHandler auth session property management."""

    def test_set_auth_session(self, user_handler):
        """Should store auth session correctly."""
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="token-abc",
            refresh_token="refresh-xyz",
            email="user@example.com",
        )

        assert user_handler.is_logged_in is True
        assert user_handler.user_id == "user-123"
        assert user_handler.user_email == "user@example.com"

    def test_clear_auth_session(self, user_handler):
        """Should clear auth session."""
        user_handler.set_auth_session(
            user_id="user-123",
            access_token="token-abc",
            refresh_token="refresh-xyz",
            email="user@example.com",
        )

        user_handler.clear_auth_session()

        assert user_handler.is_logged_in is False
        assert user_handler.user_id is None
        assert user_handler.user_email is None

    def test_auth_session_properties_without_login(self, user_handler):
        """Should return None for session properties when not logged in."""
        assert user_handler.auth_session is None
        assert user_handler.is_logged_in is False
        assert user_handler.user_id is None
        assert user_handler.user_email is None
