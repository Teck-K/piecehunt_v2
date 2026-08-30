import logging
import threading

from services.api_client import ApiError

logger = logging.getLogger(__name__)

_refresh_lock = threading.Lock()


def call_with_refresh(user_handler, api_func, *args, **kwargs):
    """Calls an api_client function, automatically refreshing the access
    token and retrying once if the call fails with a 401 (expired token).

    Args:
        user_handler: The UserHandler singleton (needs .auth_session and
            .refresh_session()).
        api_func: An api_client function whose first argument is the
            access token, e.g. update_part_quantity.
        *args, **kwargs: Passed through to api_func, after the token.

    Returns:
        Whatever api_func returns.

    Raises:
        ApiError: If the call still fails after refreshing (e.g. refresh
            token itself is also invalid/expired), or fails for any other
            reason than a 401.
    """
    token = user_handler.auth_session.access_token

    try:
        return api_func(token, *args, **kwargs)
    except ApiError as e:
        if e.status_code != 401:
            raise

        logger.info("Access token expired, refreshing session and retrying once")

        with _refresh_lock:
            if user_handler.auth_session.access_token == token:
                user_handler.refresh_session()
            else:
                logger.info("Token already refreshed by another thread, skipping")

        token = user_handler.auth_session.access_token
        return api_func(token, *args, **kwargs)
