"""
base.py - Shared HTTP session used by all collectors.

Every collector imports get_session() and safe_get() from here
so request headers, delays, and error handling are consistent.
"""

import time
import logging
import requests
from datetime import date

log = logging.getLogger(__name__)

TODAY = date.today().isoformat()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

DELAY = 2.0  # seconds between requests


def get_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def safe_get(session, url, **kwargs):
    """Make a GET request with a delay. Returns None if the request fails."""
    time.sleep(DELAY)
    try:
        response = session.get(url, timeout=15, **kwargs)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        log.warning("Request failed for %s: %s", url, e)
        return None
