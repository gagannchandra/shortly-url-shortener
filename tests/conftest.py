"""Pytest configuration and shared fixtures."""
import pytest
import mongomock
from unittest.mock import patch

from app.config import TestingConfig
from app import create_app


@pytest.fixture(scope="session")
def app():
    """Create app with testing config and mongomock database."""
    with patch("pymongo.MongoClient", mongomock.MongoClient):
        flask_app = create_app(TestingConfig)
        flask_app.config.update({
            "TESTING": True,
            "RATELIMIT_ENABLED": False,
        })
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db(app):
    """Drop URL collection before each test for isolation."""
    from app.db import get_urls_collection
    with app.app_context():
        get_urls_collection(app).drop()
    yield
    with app.app_context():
        get_urls_collection(app).drop()
