import logging
import re

from backend.helper.singletonmeta import SingletonMeta
from services.api_client import ApiError, api_login, api_refresh_auth_token, request_account_deletion
from services.auth_session import AuthSession

logger = logging.getLogger(__name__)


class UserHandler(metaclass=SingletonMeta):
    """Base class for user-related database operations."""

    def __init__(self):
        self.session = None
        self.msg = ""
        self._auth_session: AuthSession | None = None

    @property
    def auth_session(self) -> AuthSession | None:
        return self._auth_session

    @property
    def is_logged_in(self) -> bool:
        return self._auth_session is not None

    @property
    def user_id(self) -> str | None:
        return self._auth_session.user_id if self._auth_session else None

    @property
    def user_email(self) -> str | None:
        return self._auth_session.email if self._auth_session else None

    def set_auth_session(self, user_id: str, access_token: str, refresh_token: str, email: str) -> None:
        self._auth_session = AuthSession(user_id, access_token, refresh_token, email)

    def clear_auth_session(self) -> None:
        self._auth_session = None

    def reauthenticate(self, email: str, password: str) -> AuthSession | None:
        """Re-authenticate a user with email and password via the API.

        Returns:
            AuthSession on success, None on failure (wrong password, etc.)
        """
        try:
            response = api_login(email, password)
            return AuthSession(
                user_id=response["user_id"],
                access_token=response["access_token"],
                refresh_token=response["refresh_token"],
                email=response["email"],
            )
        except ApiError:
            return None  # Wrong password or other error

    def refresh_session(self) -> None:
        """Refreshes the access token using the stored refresh token via the API.

        Called automatically by call_with_refresh() when a 401 is received.
        Updates the stored auth session in place.

        Raises:
            RuntimeError: If there is no active session to refresh.
            ApiError: If the refresh token itself is invalid/expired -
                in that case the user needs to log in again.
        """
        if self._auth_session is None:
            raise RuntimeError("No session to refresh")

        try:
            response = api_refresh_auth_token(self._auth_session.refresh_token)

            # We need the user email, but the API response might not include it
            # Keep the existing email from the current session
            self.set_auth_session(
                response["user_id"],
                response["access_token"],
                response["refresh_token"],
                self._auth_session.email,  # Keep existing email
            )

            logger.info("Session refreshed for user: %s", self._auth_session.email)
        except ApiError as e:
            logger.error("Session refresh failed: %s", e)
            raise

    def delete_account(self, password: str) -> tuple[bool, str]:
        """Permanently delete the currently logged-in user's account.

        Re-authenticates the user with their password before proceeding,
        then requests deletion via the Piecehunt API.

        Args:
            password: The user's current password, used to confirm identity
                before performing this irreversible action.

        Returns:
            A tuple of (success, message). On failure, message explains why
            (e.g. incorrect password, or an API/network error).
        """
        if self.auth_session is None:
            return False, "Not logged in"

        fresh_session = self.reauthenticate(self.auth_session.email, password)
        if fresh_session is None:
            return False, "Incorrect password"

        self.set_auth_session(
            fresh_session.user_id,
            fresh_session.access_token,
            fresh_session.refresh_token,
            fresh_session.email,
        )

        try:
            request_account_deletion(self.auth_session.access_token)
        except ApiError as e:
            logger.error("Failed to delete account for %s: %s", self.auth_session.email, e)
            return False, str(e)

        logger.info("Account deleted: %s", self.auth_session.email)
        self.clear_auth_session()

        return True, "Account deleted successfully"

    def check_password_requirements(self, password: str):
        """Validates password length, character requirements and spaces."""

        if len(password) < 6:
            return False, "Password is too short (min 6 characters)."

        if len(password) > 50:
            return False, "Password is too long, how could you remember this? (max 50 characters)"

        if not any(c.isalpha() for c in password):
            return False, "Password must contain at least one letter."

        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one number."

        if " " in password:
            return False, "Password cannot contain spaces."

        return True, ""

    def check_email(self, email: str):
        """Validates email format"""

        if len(email) > 254:
            return False, "Maximum email length is 254 characters"

        email_regex = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not email_regex.match(email):
            return False, "Invalid email address."

        return True, ""
