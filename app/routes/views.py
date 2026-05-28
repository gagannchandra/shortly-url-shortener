"""
Routes that render HTML pages and handle redirects.
Kept separate from API routes because these return HTML, not JSON.
"""
from __future__ import annotations

import logging

from flask import Blueprint, abort, redirect, render_template, request

from app.services import url_service

logger = logging.getLogger(__name__)

views_bp = Blueprint("views", __name__)


@views_bp.route("/")
def index():
    """Home page — just renders the shortener form."""
    return render_template("index.html")


@views_bp.route("/about")
def about():
    """About page — a bit of background on the project."""
    return render_template("about.html")


@views_bp.route("/analytics/<string:short_code>")
def show_analytics(short_code: str):
    """Analytics dashboard for a specific short link.

    I regenerate the QR code here instead of storing it in the DB
    to save storage space. It's fast enough that this isn't a problem.

    Aborts with 404 if the code doesn't exist or has expired.
    """
    data = url_service.get_analytics(short_code)
    if data is None:
        abort(404)
    # regenerate QR on-the-fly — not worth storing in DB
    short_url = f"{request.host_url.rstrip('/')}/{short_code}"
    qr_code = url_service.generate_qr_base64(short_url)
    return render_template("analytics.html", url_data=data, qr_code=qr_code)


@views_bp.route("/<string:short_code>")
def redirect_url(short_code: str):
    """The main redirect handler — the whole point of the app.

    Records the click and sends the user to the original URL.
    Using 302 (temporary) instead of 301 (permanent) so browsers don't
    cache the redirect forever — important for analytics accuracy and
    so expired links actually show the 404 page.
    """
    long_url = url_service.perform_redirect(short_code)
    if long_url is None:
        abort(404)
    logger.info("Redirect: /%s", short_code)
    return redirect(long_url, code=302)
