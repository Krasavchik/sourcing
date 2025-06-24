"""
common/github.py
Light-weight wrapper around the public GitHub REST API v3.
Only two functions are exported: `repo()` and `owner()`.
"""

from __future__ import annotations

import os
import time
from typing import Dict, Any

import requests

# ------------------------------------------------------------------
# 0.  Config
# ------------------------------------------------------------------
TOKEN = os.getenv("TOKEN_GITHUB_API")        # supply via GH secret or .env
HEADERS = {
    "Accept": "application/vnd.github+json",
    **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
}
TIMEOUT = 10                                 # seconds per request
BASE    = "https://api.github.com"

# rudimentary rate-limit cache (per runner process)
_last_reset = 0
_remaining  = 5000


# ------------------------------------------------------------------
# 1.  Internal request helper
# ------------------------------------------------------------------
def _get(path: str) -> Dict[str, Any]:
    """
    Issue a GET to /<path>, handle rate-limit sleep, return .json().
    Raises requests.HTTPError on non-2xx.
    """
    global _last_reset, _remaining

    url = f"{BASE}/{path.lstrip('/')}"
    resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()

    # update rl counters
    _remaining = int(resp.headers.get("X-RateLimit-Remaining", _remaining))
    _last_reset = int(resp.headers.get("X-RateLimit-Reset", _last_reset))

    if _remaining == 0:               # simple blocking back-off
        sleep_for = max(0, _last_reset - time.time()) + 1
        time.sleep(sleep_for)

    return resp.json()


# ------------------------------------------------------------------
# 2.  Public helpers
# ------------------------------------------------------------------
def repo(owner: str, name: str) -> Dict[str, Any]:
    """
    `repo('openai', 'gpt-4')` → full repo JSON
    """
    return _get(f"repos/{owner}/{name}")


def owner(login: str) -> Dict[str, Any]:
    """
    Works for both user and org; GitHub decides which schema to return.
    """
    return _get(f"users/{login}")