"""Checks whether an internet connection is available.

Attempts to reach Cloudflare's DNS server (1.1.1.1) with a 3 second timeout.

Returns:
    True if a connection could be established, False otherwise.
"""

import httpx


def is_connected() -> bool:
    try:
        with httpx.Client(timeout=3.0) as client:
            client.get("https://1.1.1.1")
        return True
    except httpx.ConnectError, httpx.TimeoutException:
        return False
