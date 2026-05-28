"""
Main app factory — this is where everything gets wired together.
I learned the factory pattern from the Flask docs and honestly it makes
testing SO much easier. Worth the initial confusion.
"""
from __future__ import annotations

import logging
import logging.config
import os

from flask import Flask, jsonify, render_template


def _configure_logging(app: Flask) -> None:
    """Set up logging so I can actually see what's happening.

    In dev mode, prints readable logs to the terminal.
    In production, outputs JSON so log aggregators can parse it properly.
    Took me a while to figure out dictConfig but it's cleaner than basicConfig.
    """
    level = app.config.get("LOG_LEVEL", "INFO")
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                # structured JSON format for production log parsers
                "format": (
                    '{"time":"%(asctime)s","level":"%(levelname)s",'
                    '"logger":"%(name)s","message":"%(message)s"}'
                )
            },
            "dev": {
                # readable format for local dev — much nicer to look at
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "dev" if app.debug else "json",
            }
        },
        "root": {"level": level, "handlers": ["console"]},
    })


def create_app(config_object=None) -> Flask:
    """App factory — creates and configures the Flask app.

    I use a factory function instead of a global app instance so tests
    can spin up fresh isolated apps. Learned this the hard way after
    tests were sharing state and breaking each other 😅

    Args:
        config_object: pass a config class directly (useful for tests).
                       If None, it picks one based on FLASK_ENV.

    Returns:
        Flask: fully wired-up app, ready to serve requests.
    """
    app = Flask(__name__, instance_relative_config=False)

    # load config first — everything else depends on it
    if config_object is None:
        from app.config import get_config
        config_object = get_config()
    app.config.from_object(config_object)

    _configure_logging(app)

    # connect to MongoDB and create indexes if they don't exist
    from app.db import init_db
    init_db(app)

    # rate limiting — bhai koi 1000 requests/sec bhej ke server nahi girayega
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get("RATELIMIT_STORAGE_URI", "memory://"),
        headers_enabled=True,  # sends X-RateLimit-* headers so clients know their limit
    )

    # security headers via Flask-Talisman
    # CSP was confusing at first — basically tells the browser what sources are trusted
    from flask_talisman import Talisman

    csp = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "'unsafe-inline'"],   # needed for inline JS handlers
        "style-src": ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com", "https://fonts.googleapis.com"],
        "img-src": ["'self'", "data:"],   # data: is for base64 QR code images
        "connect-src": ["'self'"],
        "frame-ancestors": ["'none'"],    # prevent clickjacking
    }
    Talisman(
        app,
        force_https=app.config.get("FORCE_HTTPS", False),
        content_security_policy=csp,
        referrer_policy="strict-origin-when-cross-origin",
        feature_policy={"geolocation": "'none'"},
    )

    # register blueprints — api routes and page routes live in separate files
    from app.routes.api import api_bp
    from app.routes.views import views_bp

    app.register_blueprint(api_bp)
    app.register_blueprint(views_bp)

    # tighter rate limit on shorten endpoint specifically
    # NOTE: must do this AFTER registering blueprints, otherwise view_functions won't exist yet
    limiter.limit("10 per minute; 100 per hour")(
        app.view_functions["api.shorten_url"]
    )

    # global error handlers — return JSON for API requests, HTML for browser requests
    @app.errorhandler(404)
    def not_found(e):
        if _is_api_request():
            return jsonify({"error": "Resource not found.", "status": 404}), 404
        return render_template("404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(e):
        if _is_api_request():
            return jsonify({"error": "Rate limit exceeded. Please slow down.", "status": 429}), 429
        return render_template("429.html"), 429

    @app.errorhandler(500)
    def server_error(e):
        if _is_api_request():
            return jsonify({"error": "Internal server error.", "status": 500}), 500
        return render_template("500.html"), 500

    return app


def _is_api_request() -> bool:
    """Check if the current request is hitting an API endpoint.

    Used by error handlers to decide whether to send JSON or an HTML page.
    Simple path prefix check + content-type check covers most cases.
    """
    from flask import request
    return request.path.startswith("/api/") or request.is_json
