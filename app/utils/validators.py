"""
Input validation helpers. I validate on both the client side (JS) and
server side (here) because never trust the frontend — anyone can
send raw API requests and bypass the JS entirely.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

import validators

# only letters, numbers, hyphens, underscores — no spaces or special chars
_ALIAS_RE = re.compile(r"^[a-zA-Z0-9_-]+$")

# codes that would clash with actual routes in the app — can't use these as aliases
RESERVED_CODES = frozenset({
    "api", "analytics", "static", "health", "favicon.ico",
    "robots.txt", "sitemap.xml", "admin", "login", "logout",
})


def validate_url(url: str) -> tuple[str, str | None]:
    """Validates and normalizes a URL submitted by the user.

    Auto-adds https:// if the user didn't include a scheme — most people
    just type 'example.com' without the protocol prefix.

    Returns a tuple of (normalized_url, error_message).
    error_message is None if the URL is valid.
    """
    if not url:
        return url, "URL is required."
    if len(url) > 2048:
        return url, "URL is too long (max 2048 characters)."

    # be nice to users — add https:// if they forgot
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return url, "Invalid URL format."

    if parsed.scheme not in ("http", "https"):
        return url, "URL must start with http:// or https://."

    if not parsed.netloc:
        return url, "URL must include a valid hostname."

    # strip port number before checking for dots (e.g. localhost:8080)
    hostname = parsed.hostname or ""
    if "." not in hostname and hostname != "localhost":
        return url, "URL must include a valid domain (e.g., example.com)."

    # final check using the validators library
    if not validators.url(url):
        return url, "Please enter a valid URL."

    return url, None


def validate_alias(alias: str, min_len: int = 4, max_len: int = 30) -> str | None:
    """Validates a custom alias chosen by the user.

    Returns an error message string if invalid, None if it's good to go.
    Checks: not empty, not reserved, correct length, allowed characters.
    """
    if not alias:
        return "Custom alias cannot be empty."
    if alias.lower() in RESERVED_CODES:
        return f"'{alias}' is a reserved word and cannot be used as an alias."
    if not (min_len <= len(alias) <= max_len):
        return f"Alias must be between {min_len} and {max_len} characters."
    if not _ALIAS_RE.match(alias):
        return "Alias may only contain letters, numbers, hyphens, and underscores."
    return None


def validate_ttl(ttl_days: int | None) -> str | None:
    """Validates the TTL (time-to-live) value.

    Must be an integer between 1 and 365. Anything else gets rejected.
    Returns None if valid, error string if not.
    """
    if ttl_days is None:
        return None
    if not isinstance(ttl_days, int) or not (1 <= ttl_days <= 365):
        return "ttl_days must be an integer between 1 and 365."
    return None
