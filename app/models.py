"""
Data access layer — all MongoDB reads/writes go through here.
I wanted to keep DB logic out of the service layer, so this module
is the only place that directly touches the collection.
"""
from __future__ import annotations

import datetime
from typing import Any

from app.db import get_urls_collection


# This is what a document looks like in MongoDB (for my own reference):
# {
#   "_id":             ObjectId,
#   "long_url":        str,        # the original long URL the user submitted
#   "short_code":      str,        # the 6-char code (or custom alias)
#   "created_at":      datetime,   # UTC timestamp when it was created
#   "expires_at":      datetime | None,  # None = never expires
#   "clicks":          int,        # total redirect count
#   "daily_clicks":    {           # per-day click counts for the chart
#       "2024-01-15": 5,
#       ...
#   },
#   "last_clicked_at": datetime | None,
# }


def _now() -> datetime.datetime:
    """Returns the current time in UTC. Always use this instead of datetime.now()
    to avoid timezone headaches with MongoDB.
    """
    return datetime.datetime.now(datetime.timezone.utc)


def _today_key() -> str:
    """Returns today's date as a string like '2024-01-15'.
    Used as the key in the daily_clicks map for analytics.
    """
    return _now().strftime("%Y-%m-%d")


# ── Serialization ────────────────────────────────────────────────────────────

def serialize(doc: dict[str, Any]) -> dict[str, Any]:
    """Converts a raw MongoDB document into something JSON-serializable.

    Main issues to fix:
    - _id is an ObjectId, not a string
    - datetime fields need to be ISO format strings
    """
    if doc is None:
        return {}
    result = {k: v for k, v in doc.items()}
    result["id"] = str(result.pop("_id", ""))
    if isinstance(result.get("created_at"), datetime.datetime):
        result["created_at"] = result["created_at"].isoformat()
    if isinstance(result.get("expires_at"), datetime.datetime):
        result["expires_at"] = result["expires_at"].isoformat()
    if isinstance(result.get("last_clicked_at"), datetime.datetime):
        result["last_clicked_at"] = result["last_clicked_at"].isoformat()
    return result


# ── Read operations ──────────────────────────────────────────────────────────

def find_by_code(short_code: str) -> dict[str, Any] | None:
    """Look up a URL entry by its short code.

    Returns the full document, or None if the code doesn't exist
    (or was already TTL-deleted by MongoDB).
    """
    return get_urls_collection().find_one({"short_code": short_code})


def find_by_long_url(long_url: str) -> dict[str, Any] | None:
    """Check if we already have a short link for this URL (no-expiry only).

    Only matches permanent links (expires_at = None) to avoid returning
    a link that's about to expire as if it were permanent.
    """
    return get_urls_collection().find_one({"long_url": long_url, "expires_at": None})


def code_exists(short_code: str) -> bool:
    """Quick check to see if a short code is already taken.

    Uses limit=1 so MongoDB stops scanning after the first match.
    """
    return get_urls_collection().count_documents(
        {"short_code": short_code}, limit=1
    ) > 0


# ── Write operations ─────────────────────────────────────────────────────────

def create_url_entry(
    long_url: str,
    short_code: str,
    expires_at: datetime.datetime | None = None,
) -> dict[str, Any]:
    """Insert a new URL document into the collection.

    Raises DuplicateKeyError if the short_code is already taken
    (the unique index enforces this at the DB level).
    """
    doc = {
        "long_url": long_url,
        "short_code": short_code,
        "created_at": _now(),
        "expires_at": expires_at,
        "clicks": 0,
        "daily_clicks": {},   # starts empty, gets populated on each redirect
        "last_clicked_at": None,
    }
    result = get_urls_collection().insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def record_click(short_code: str) -> None:
    """Increments click counters atomically using $inc.

    $inc is atomic in MongoDB so concurrent requests won't cause
    race conditions on the counter.
    """
    today = _today_key()
    get_urls_collection().update_one(
        {"short_code": short_code},
        {
            "$inc": {
                "clicks": 1,
                f"daily_clicks.{today}": 1,
            },
            "$set": {"last_clicked_at": _now()},
        },
    )


def delete_by_code(short_code: str) -> bool:
    """Deletes a URL entry by short code. Returns True if something was deleted."""
    result = get_urls_collection().delete_one({"short_code": short_code})
    return result.deleted_count > 0
