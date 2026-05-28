"""
Core business logic for URL shortening. This is the main "brain" of the app.
The routes just call functions from here — keeping the actual logic separate
from request/response handling made things much easier to test.
"""
from __future__ import annotations

import datetime
import secrets
import string
import io
import base64
import logging
from typing import Any

import segno
from pymongo.errors import DuplicateKeyError

from app import models
from app.config import Config

logger = logging.getLogger(__name__)

# base62 charset — only alphanumeric chars, no confusing symbols
_CHARSET = string.ascii_letters + string.digits


# ── Short code generation ────────────────────────────────────────────────────

def generate_short_code(length: int = 6) -> str:
    """Generates a random short code using cryptographically secure randomness.

    Using secrets.choice instead of random.choice because random is
    predictable — someone could theoretically guess codes if I used it.
    6 chars from 62 gives 62^6 = ~56 billion combinations, so collisions
    are very rare but not impossible (handled by _unique_code).
    """
    return "".join(secrets.choice(_CHARSET) for _ in range(length))


def _unique_code(length: int, max_retries: int) -> str:
    """Tries to generate a short code that isn't already taken.

    Keeps retrying until it finds a free one or hits max_retries.
    At 62^6 possible codes, collisions should basically never happen,
    but it's good to handle it properly anyway.

    Raises:
        RuntimeError: if we somehow exhaust all retries (extremely unlikely).
    """
    for attempt in range(max_retries):
        code = generate_short_code(length)
        if not models.code_exists(code):
            return code
        # log collisions so I can see if the DB is getting too full
        logger.warning("Short code collision on attempt %d: %s", attempt + 1, code)

    raise RuntimeError(
        f"Could not generate unique short code after {max_retries} attempts."
    )


# ── QR code ──────────────────────────────────────────────────────────────────

def generate_qr_base64(url: str) -> str:
    """Generates a QR code for the URL and returns it as a base64 data URI.

    I picked segno over qrcode library because it's smaller and has
    better output quality. The base64 encoding lets me embed the image
    directly in the HTML/JSON response without needing a separate file.
    """
    buffer = io.BytesIO()
    segno.make(url, error='m').save(
        buffer, kind='png', scale=8, border=2,
        dark='#09090b', light='#f8fafc'   # matches the app's dark theme
    )
    encoded = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


# ── Main shortening logic ────────────────────────────────────────────────────

def shorten(
    long_url: str,
    custom_alias: str | None,
    ttl_days: int | None,
    host_url: str,
    code_length: int = Config.SHORT_CODE_LENGTH,
    max_retries: int = Config.MAX_RETRIES_SHORT_CODE,
) -> dict[str, Any]:
    """Creates a new short URL. This is the core function of the whole project.

    Steps:
    1. Calculate expiry date if TTL was provided
    2. Use custom alias or generate a random code
    3. Save to DB (handle the rare race condition via DuplicateKeyError)
    4. Generate QR code and return everything the frontend needs

    Args:
        long_url: the original URL to shorten.
        custom_alias: optional user-chosen alias (e.g. "my-link").
        ttl_days: how many days until the link expires (None = permanent).
        host_url: base URL of the app, used to build the final short URL.
        code_length: length of random codes (default from config).
        max_retries: how many times to retry on collision.

    Returns:
        dict with short_url, short_code, analytics_url, qr_code, created_at, expires_at.

    Raises:
        ValueError: bad TTL value, or custom alias is already taken.
        RuntimeError: couldn't find a unique code after max_retries (super rare).
    """
    expires_at: datetime.datetime | None = None
    if ttl_days is not None:
        if not (1 <= ttl_days <= 365):
            raise ValueError("ttl_days must be between 1 and 365.")
        expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=ttl_days
        )

    if custom_alias:
        # check availability before trying to insert (better error message this way)
        if models.code_exists(custom_alias):
            raise ValueError("This custom alias is already in use. Please choose another.")
        short_code = custom_alias
    else:
        short_code = _unique_code(code_length, max_retries)

    try:
        doc = models.create_url_entry(long_url, short_code, expires_at)
    except DuplicateKeyError:
        # race condition: two requests generated the same code at the same time
        # extremely unlikely but the unique index will catch it
        raise ValueError("Short code conflict. Please try again.")

    short_url = f"{host_url.rstrip('/')}/{short_code}"

    return {
        "short_url": short_url,
        "short_code": short_code,
        "analytics_url": f"{host_url.rstrip('/')}/analytics/{short_code}",
        "qr_code": generate_qr_base64(short_url),
        "created_at": doc["created_at"].isoformat(),
        "expires_at": doc["expires_at"].isoformat() if doc["expires_at"] else None,
    }


def get_analytics(short_code: str) -> dict[str, Any]:
    """Fetches analytics data for a short code, including a 14-day chart.

    Builds the chart_data array by iterating the last 14 days and looking
    up each date in daily_clicks. Days with no clicks get a 0 so the
    chart always has a full 14 bars.
    """
    doc = models.find_by_code(short_code)
    if not doc:
        return None

    # build 14-day chart — iterate from 13 days ago to today
    today = datetime.date.today()
    daily_clicks = doc.get("daily_clicks", {})
    chart_data = []
    for i in range(13, -1, -1):
        day = today - datetime.timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        chart_data.append({"date": key, "clicks": daily_clicks.get(key, 0)})

    return {
        **models.serialize(doc),
        "chart_data": chart_data,
    }


def perform_redirect(short_code: str) -> str | None:
    """Looks up the long URL and records the click in a single atomic operation.

    I originally did find() then update() separately, but that has a race
    condition — the doc could expire between the two calls. find_one_and_update
    fixes this by doing both in one atomic DB operation.

    Returns the long URL if found, None if the code doesn't exist or expired.
    """
    from app.db import get_urls_collection
    from pymongo import ReturnDocument

    today = datetime.date.today().strftime("%Y-%m-%d")
    now = datetime.datetime.now(datetime.timezone.utc)

    doc = get_urls_collection().find_one_and_update(
        {"short_code": short_code},
        {
            "$inc": {"clicks": 1, f"daily_clicks.{today}": 1},
            "$set": {"last_clicked_at": now},
        },
        return_document=ReturnDocument.BEFORE,  # return the doc as it was before update
    )
    if not doc:
        return None
    return doc["long_url"]
