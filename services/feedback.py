"""Feedback reporting service for the PieceHunt app.

Sends feedback reports to the API, which handles email delivery.
"""

import logging
from pathlib import Path

import httpx

from services.api_client import ApiError
from settings import API_BASE_URL

logger = logging.getLogger(__name__)

_FEEDBACK_URL = f"{API_BASE_URL}/feedback/report"


def report_feedback(
    access_token: str,
    feedback_type: str,
    description: str,
    include_logs: bool = False,
    image_path: Path | None = None,
) -> dict:
    """Send a feedback report to the API.

    Args:
        access_token: A valid Supabase access token for the requesting user.
        feedback_type: One of 'missing_image', 'false_positive', 'app_error', 'other'.
        description: A description of the issue.
        include_logs: Whether to attach the app log file to the report.
        image_path: Optional path to an image file (only used for false_positive reports).

    Returns:
        The parsed JSON response from the API on success.

    Raises:
        ApiError: On any failure (server error, network error).
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "type": feedback_type,
        "description": description,
        "include_logs": include_logs,
    }

    try:
        logger.info("image_path: %s, exists: %s", image_path, image_path.exists() if image_path else None)
        if image_path and image_path.exists():
            with open(image_path, "rb") as f:
                response = httpx.post(
                    _FEEDBACK_URL,
                    data=data,
                    files={"image": (image_path.name, f, "image/png")},
                    headers=headers,
                    timeout=30.0,
                )
        else:
            response = httpx.post(
                _FEEDBACK_URL,
                data=data,
                headers=headers,
                timeout=30.0,
            )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text or str(e.response.status_code)
        logger.error(
            "Report feedback failed with status %s: %s",
            e.response.status_code,
            detail,
        )
        raise ApiError(detail, e.response.status_code) from e
    except httpx.RequestError as e:
        logger.error("Report feedback request failed: %s", e)
        raise ApiError(f"Could not reach server: {e}") from e

    return response.json()
