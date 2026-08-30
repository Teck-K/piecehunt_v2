import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RegisterResult:
    """Result of a registration attempt via Supabase Auth.

    Attributes:
        success: Whether the sign-up call succeeded.
        needs_email_confirmation: True if the user still needs to confirm
            their email before they can log in (confirm-email enabled).
        user_id: Supabase auth UUID of the newly created user, if known.
        access_token: JWT access token, only set if the user is
            immediately logged in (confirm-email disabled).
        refresh_token: Refresh token, only set alongside access_token.
        error: Human-readable error message if success is False.
    """

    success: bool
    needs_email_confirmation: bool
    user_id: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    email: str | None = None
    error: str | None = None


@dataclass
class LoginResult:
    """Result of a login attempt via Supabase Auth.

    Attributes:
        success: Whether the login succeeded.
        user_id: Supabase auth UUID of the logged-in user.
        access_token: JWT access token for the new session.
        refresh_token: Refresh token for the new session.
        error: Human-readable error message if success is False.
    """

    success: bool
    user_id: str | None = None
    access_token: str | None = None
    refresh_token: str | None = None
    email: str | None = None
    error: str | None = None


def login(email: str, password: str) -> LoginResult:
    """Log in a user via the Piecehunt API."""
    from services.api_client import ApiError, api_login

    try:
        response = api_login(email, password)
        logger.info("User logged in: %s", email)
        return LoginResult(
            success=True,
            user_id=response["user_id"],
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
            email=email,
        )
    except ApiError as e:
        logger.warning("Login failed for email: %s (%s)", email, e)
        return LoginResult(success=False, error=str(e))


def register(email: str, password: str) -> RegisterResult:
    """Register a new user via the Piecehunt API."""
    from services.api_client import ApiError, api_register

    try:
        response = api_register(email, password)
        logger.info("User registered: %s", email)
        return RegisterResult(
            success=response["success"],
            needs_email_confirmation=response["needs_email_confirmation"],
            user_id=response.get("user_id"),
            access_token=response.get("access_token"),
            refresh_token=response.get("refresh_token"),
            email=email,
            error=response.get("error"),
        )
    except ApiError as e:
        logger.warning("Registration failed for email: %s (%s)", email, e)
        return RegisterResult(
            success=False,
            needs_email_confirmation=False,
            error=str(e),
        )
