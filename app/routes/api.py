"""
REST API endpoints for Shortly.
I put these in a Blueprint so they're separate from the page routes
and easier to manage. All routes here are under the /api prefix.
"""
from __future__ import annotations

import logging

from flask import Blueprint, jsonify, request, current_app

from app.services import url_service
from app.utils.validators import validate_url, validate_alias, validate_ttl

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _err(message: str, status: int = 400):
    """Helper to build a consistent error response.
    Saves me from repeating the same jsonify structure everywhere.
    """
    return jsonify({"error": message, "status": status}), status


def _ok(data: dict, status: int = 200):
    """Helper to build a consistent success response."""
    return jsonify({"data": data, "status": status}), status


@api_bp.route("/health", methods=["GET", "HEAD"])
def health():
    """Simple health check — checks if MongoDB is still breathing.

    Added HEAD method because UptimeRobot needs it!
    Bhai agar database down hai toh seedha 503 .
    """
    from app.db import get_client
    try:
        get_client().admin.command("ping")
        db_status = "ok"
    except Exception as e:
        logger.error("Health check DB ping failed: %s", e)
        db_status = "error"

    status = 200 if db_status == "ok" else 503
    return jsonify({
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "service": "shortly",
    }), status


@api_bp.route("/shorten", methods=["POST"])
def shorten_url():
    """Takes a long URL and returns a short one.

    Expected JSON body:
        { "long_url": "...", "custom_alias": "...", "ttl_days": 7 }
    custom_alias and ttl_days are optional.

    Returns 201 on success, 400 for bad input, 409 if alias is taken.
    """
    data = request.get_json(silent=True)
    if not data:
        return _err("Request body must be valid JSON.", 400)

    # validate the URL — also normalises it (adds https:// if missing)
    raw_url = (data.get("long_url") or "").strip()
    normalised_url, url_error = validate_url(raw_url)
    if url_error:
        return _err(url_error, 400)

    # custom alias is optional — skip validation if not provided
    custom_alias = (data.get("custom_alias") or "").strip() or None
    if custom_alias:
        alias_error = validate_alias(
            custom_alias,
            min_len=current_app.config["MIN_CUSTOM_ALIAS_LENGTH"],
            max_len=current_app.config["MAX_CUSTOM_ALIAS_LENGTH"],
        )
        if alias_error:
            return _err(alias_error, 400)

    # TTL is also optional — if provided, must be an int between 1 and 365
    ttl_days = data.get("ttl_days")
    if ttl_days is not None:
        try:
            ttl_days = int(ttl_days)
        except (TypeError, ValueError):
            return _err("ttl_days must be a positive integer.", 400)
        ttl_error = validate_ttl(ttl_days)
        if ttl_error:
            return _err(ttl_error, 400)

    # call the service layer — this does the actual work
    try:
        result = url_service.shorten(
            long_url=normalised_url,
            custom_alias=custom_alias,
            ttl_days=ttl_days,
            host_url=request.host_url,
            code_length=current_app.config["SHORT_CODE_LENGTH"],
            max_retries=current_app.config["MAX_RETRIES_SHORT_CODE"],
        )
    except ValueError as exc:
        # alias conflict gets a 409, everything else is a 400
        status = 409 if "alias" in str(exc).lower() or "conflict" in str(exc).lower() else 400
        return _err(str(exc), status)
    except RuntimeError as exc:
        logger.error("Short code generation failed: %s", exc)
        return _err("Failed to generate a short code. Please try again.", 500)

    logger.info("Created short URL: %s → %s", result["short_code"], normalised_url[:80])
    return _ok(result, 201)


@api_bp.route("/analytics/<string:short_code>")
def get_analytics(short_code: str):
    """Returns analytics data for a given short code as JSON.

    The analytics page (HTML) fetches this to populate the chart.
    Returns 404 if the code doesn't exist or expired.
    """
    data = url_service.get_analytics(short_code)
    if data is None:
        return _err("Short URL not found.", 404)
    return _ok(data)
