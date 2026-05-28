"""
MongoDB connection setup. Handles creating the client, getting collections,
and setting up indexes. I made everything go through this module so there's
one single place managing the DB connection.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

if TYPE_CHECKING:
    from flask import Flask

logger = logging.getLogger(__name__)

# global client instance — shared across the whole app (connection pooling)
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Returns the MongoDB client. Crashes loudly if init_db() wasn't called first.

    I store the client as a module-level global so the connection pool
    is shared across all requests instead of reconnecting every time.
    """
    global _client
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db(app) first.")
    return _client


def get_db(app=None):
    """Gets the actual database object from the client.

    Accepts an optional app param for cases where current_app isn't available
    (like during index creation at startup).
    """
    from flask import current_app
    ctx_app = app or current_app
    return get_client()[ctx_app.config["MONGO_DB_NAME"]]


def get_urls_collection(app=None) -> Collection:
    """Returns the 'urls' collection — the only collection this app uses."""
    return get_db(app)["urls"]


def init_db(app: Flask) -> None:
    """Connect to MongoDB and set up indexes. Called once at app startup.

    I set timeouts so the app fails fast if MongoDB is unreachable
    instead of hanging for 30 seconds.

    Raises:
        ConnectionFailure: if MongoDB can't be reached at all.
    """
    global _client

    uri = app.config["MONGO_URI"]
    try:
        _client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,   # fail after 5s if can't find a server
            maxPoolSize=50,                   # max concurrent connections
            minPoolSize=5,                    # keep at least 5 alive
            connectTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
        # ping to actually verify the connection works
        _client.admin.command("ping")
        logger.info("MongoDB connection established.")
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.critical("Failed to connect to MongoDB: %s", e)
        raise

    _create_indexes(app)


def _create_indexes(app: Flask) -> None:
    """Make sure the indexes exist. Running this at startup is safe — MongoDB
    skips creation if they already exist.

    Two indexes:
    1. unique index on short_code for fast lookups
    2. TTL index on expires_at — MongoDB automatically deletes expired docs!
       This was the coolest thing I learned while building this project.
    """
    urls = get_urls_collection(app)

    # main lookup index — every redirect hits this
    urls.create_index([("short_code", ASCENDING)], unique=True, name="idx_short_code")

    # TTL index — when expires_at < now, MongoDB deletes the doc automatically
    # sparse=True means docs without expires_at are ignored (permanent links)
    urls.create_index(
        [("expires_at", ASCENDING)],
        expireAfterSeconds=0,
        sparse=True,
        name="idx_ttl_expiry",
    )

    logger.info("MongoDB indexes ensured.")


def close_db() -> None:
    """Closes the MongoDB connection. Mostly used in cleanup/teardown."""
    global _client
    if _client:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed.")
