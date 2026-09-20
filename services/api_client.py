"""Thin HTTP layer for talking to the Piecehunt API.

Handlers (e.g. UserHandler) call these functions instead of using
httpx directly. This keeps all request/response/error handling for
our own API in one place.
"""

import logging
from pathlib import Path

import httpx

from settings import API_BASE_URL

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised when a call to the Piecehunt API fails.

    Attributes:
        status_code: The HTTP status code, if the server responded
            at all (None if the request never reached the server,
            e.g. a connection error).
    """

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def request_account_deletion(access_token: str) -> dict:
    """Delete the currently authenticated user's account.

    Args:
        access_token: A valid Supabase access token for the user
            requesting deletion.

    Returns:
        The parsed JSON response from the API on success.

    Raises:
        ApiError: If the request fails, either because the server
            returned an error status or because it could not be
            reached at all.
    """
    try:
        response = httpx.delete(
            f"{API_BASE_URL}/accounts/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Delete account failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to delete account: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Delete account request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    logger.info("Account deleted successfully via API")
    return response.json()


def get_set_status(access_token: str, set_num: str) -> dict | None:
    """Check whether a set exists, and whether the current user already added it.

    Args:
        access_token: A valid Supabase access token for the requesting user.
        set_num: The set number without suffix (e.g. '42154').

    Returns:
        None if the set doesn't exist in the catalog.
        Otherwise, a dict with keys "already_added" (bool) and "set" (dict).

    Raises:
        ApiError: If the request fails for a reason other than "set not
            found" (e.g. a server error or network issue).
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/sets/{set_num}/status",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Set status request failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to check set status: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Set status request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def add_user_set(access_token: str, set_num: str) -> dict:
    """Adds a set to the current user's collection.

    Args:
        access_token: A valid Supabase access token for the requesting user.
        set_num: The set number without suffix (e.g. '42154').

    Returns:
        A dict with user_set_id, set info, and part/minifig image URLs
        needed to download images locally.

    Raises:
        ApiError: On any failure (not found, already added, server error, network).
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/sets/{set_num}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        logger.error("Add set failed with status %s: %s", e.response.status_code, detail)
        raise ApiError(detail, e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Add set request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def get_my_sets(access_token: str, include_spares: bool = True) -> list:
    """Fetches all sets belonging to the current user, with progress info.

    Args:
        access_token: A valid Supabase access token for the requesting user.
        include_spares: Whether spare parts count towards progress.

    Returns:
        A list of dicts describing each set (see routers/sets.py:get_my_sets).

    Raises:
        ApiError: On any failure.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/sets/mine",
            params={"include_spares": include_spares},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Get my sets failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to fetch sets: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Get my sets request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def get_user_set(access_token: str, user_set_id: int) -> dict | None:
    """Fetches a single user set by id. Returns None if not found (or not yours)."""
    try:
        response = httpx.get(
            f"{API_BASE_URL}/sets/{user_set_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Get user set failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to fetch set: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Get user set request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def delete_user_set(access_token: str, user_set_id: int) -> dict:
    """Deletes a user set by id.

    Raises:
        ApiError: If the set doesn't exist (or isn't yours), or on server/network error.
    """
    try:
        response = httpx.delete(
            f"{API_BASE_URL}/sets/{user_set_id}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        logger.error("Delete user set failed with status %s: %s", e.response.status_code, detail)
        raise ApiError(detail, e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Delete user set request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def get_userset_parts(access_token: str, user_set_id: int) -> list:
    """Fetches all parts for a user's set, with progress and metadata.

    Raises:
        ApiError: If the set doesn't exist (or isn't yours), or on server/network error.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/sets/{user_set_id}/parts",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Get userset parts failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to fetch parts: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Get userset parts request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def get_userset_minifigs(access_token: str, user_set_id: int) -> list:
    """Fetches all minifigures for a user's set.

    Raises:
        ApiError: If the set doesn't exist (or isn't yours), or on server/network error.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/sets/{user_set_id}/minifigs",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Get userset minifigs failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to fetch minifigs: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Get userset minifigs request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def get_userset_colors(access_token: str, user_set_id: int) -> list:
    """Fetches the distinct colors used across a user's set.

    Raises:
        ApiError: If the set doesn't exist (or isn't yours), or on server/network error.
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/sets/{user_set_id}/colors",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Get userset colors failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to fetch colors: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Get userset colors request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def update_part_quantity(access_token: str, user_set_id: int, userpart_id: int, quantity: int) -> dict:
    """Updates the found quantity for a single part.

    Raises:
        ApiError: If the part/set doesn't exist (or isn't yours), or on server/network error.
    """
    try:
        response = httpx.patch(
            f"{API_BASE_URL}/sets/{user_set_id}/parts/{userpart_id}",
            json={"quantity": quantity},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Update part quantity failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to update quantity: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Update part quantity request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def apply_parts_action(access_token: str, user_set_id: int, action: str) -> dict:
    """Applies a bulk action ('reset_set' or 'complete_set') to all parts in a set.

    Raises:
        ApiError: If the set doesn't exist (or isn't yours), or on server/network error.
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/sets/{user_set_id}/parts/actions",
            json={"action": action},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        logger.error("Apply parts action failed with status %s: %s", e.response.status_code, detail)
        raise ApiError(detail, e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Apply parts action request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def email_missing_parts_report(
    access_token: str,
    file_path: Path,
    part_count: int,
    set_count: int,
    include_spares: bool,
) -> dict:
    """Uploads a generated missing parts report and has the API email it
    to the current user.

    Args:
        access_token: A valid Supabase access token for the requesting user.
        file_path: Path to the generated report file (PDF or Excel).
        part_count: Number of unique missing parts in the report.
        set_count: Number of sets included in the report.
        include_spares: Whether spare parts were included.

    Raises:
        ApiError: On any failure (server error, network error).
    """
    try:
        with open(file_path, "rb") as f:
            response = httpx.post(
                f"{API_BASE_URL}/reports/missing-parts/email",
                files={"file": (file_path.name, f, "application/octet-stream")},
                data={
                    "part_count": part_count,
                    "set_count": set_count,
                    "include_spares": include_spares,
                },
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=30.0,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        logger.error("Email missing parts report failed with status %s: %s", e.response.status_code, detail)
        raise ApiError(detail, e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Email missing parts report request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def request_email_verification(access_token: str) -> dict:
    """Request a verification email for the currently authenticated user.

    Args:
        access_token: A valid Supabase access token for the requesting user.

    Returns:
        The parsed JSON response from the API on success.

    Raises:
        ApiError: On any failure (server error, network error).
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/auth/email-verification/request",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Request email verification failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to request email verification: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Request email verification request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def get_email_verification_status(access_token: str) -> dict:
    """Check whether the current user's email address is verified.

    Args:
        access_token: A valid Supabase access token for the requesting user.

    Returns:
        A dict with key "email_verified" (bool).

    Raises:
        ApiError: On any failure (server error, network error).
    """
    try:
        response = httpx.get(
            f"{API_BASE_URL}/auth/email-verification/status",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Get email verification status failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to get verification status: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Get email verification status request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def request_password_reset(email: str) -> dict:
    """Request a password reset link for the given email address.

    No access token required: the user is by definition not logged in.

    Args:
        email: The email address of the account to reset.

    Returns:
        The parsed JSON response from the API on success.

    Raises:
        ApiError: On any failure (server error, network error).
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/auth/password-reset/request",
            json={"email": email},
            timeout=30.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Request password reset failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Failed to request password reset: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Request password reset request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def api_login(email: str, password: str) -> dict:
    """Sign in with email and password.

    Returns a dict with user_id, access_token, refresh_token, and email.

    Raises:
        ApiError: If login fails (invalid credentials, etc.)
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Login failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Login failed: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Login request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def api_register(email: str, password: str) -> dict:
    """Register a new user with email and password.

    Returns a dict with success status, needs_email_confirmation,
    and optional tokens/user_id.

    Raises:
        ApiError: If registration fails (email exists, etc.)
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/auth/register",
            json={"email": email, "password": password},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        logger.error("Registration failed with status %s: %s", e.response.status_code, detail)
        raise ApiError(detail, e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Registration request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()


def api_refresh_auth_token(refresh_token: str) -> dict:
    """Refresh an access token using a refresh token.

    Returns a dict with access_token, refresh_token, and user_id.

    Raises:
        ApiError: If refresh fails (invalid token, etc.)
    """
    try:
        response = httpx.post(
            f"{API_BASE_URL}/auth/refresh",
            json={"refresh_token": refresh_token},
            timeout=10.0,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error("Token refresh failed with status %s: %s", e.response.status_code, e.response.text)
        raise ApiError(f"Token refresh failed: {e.response.status_code}", e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Token refresh request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()
