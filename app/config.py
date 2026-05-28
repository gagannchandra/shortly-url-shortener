"""
All the config lives here. I kept hitting issues where dev and prod
settings were mixed up, so I split them into separate classes.
Learned about the factory pattern from the Flask docs — game changer.
"""
from __future__ import annotations

import os
from dotenv import load_dotenv

# load .env file so I don't have to set env vars manually every time
load_dotenv()


class Config:
    """Base config with sensible defaults.

    Both DevelopmentConfig and ProductionConfig inherit from this.
    I tried to keep sane defaults so the app at least runs locally
    without needing to set every single variable.
    """
    # -- Core --
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-CHANGE-IN-PRODUCTION")
    DEBUG: bool = False
    TESTING: bool = False

    # -- MongoDB --
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/shortly")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "shortly")

    # -- App Settings --
    SHORT_CODE_LENGTH: int = int(os.getenv("SHORT_CODE_LENGTH", "6"))
    MAX_RETRIES_SHORT_CODE: int = 10          # retry up to 10 times if code collides
    MAX_CUSTOM_ALIAS_LENGTH: int = 30
    MIN_CUSTOM_ALIAS_LENGTH: int = 4
    DEFAULT_LINK_TTL_DAYS: int | None = None  # None means links never expire by default

    # -- Rate Limiting --
    RATELIMIT_DEFAULT: str = "200 per day;50 per hour"
    RATELIMIT_STORAGE_URI: str = os.getenv("REDIS_URL", "memory://")  # use redis in prod
    RATELIMIT_HEADERS_ENABLED: bool = True

    # -- Security --
    FORCE_HTTPS: bool = os.getenv("FORCE_HTTPS", "false").lower() == "true"
    ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # -- Logging --
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Config for local development — debug mode on so I can see errors."""
    DEBUG = True


class TestingConfig(Config):
    """Config used when running pytest.

    Points to a separate test DB so tests don't mess with real data.
    Also disables rate limiting so tests don't randomly fail.
    """
    TESTING = True
    MONGO_URI = "mongodb://localhost:27017/shortly_test"
    MONGO_DB_NAME = "shortly_test"
    RATELIMIT_ENABLED = False
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production config — forces HTTPS because security matters."""
    FORCE_HTTPS = True


# map FLASK_ENV strings to config classes
_configs: dict[str, type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config() -> type[Config]:
    """Pick the right config based on the FLASK_ENV environment variable.

    Falls back to DevelopmentConfig if the env isn't set or is unrecognized.
    """
    env = os.getenv("FLASK_ENV", "default")
    return _configs.get(env, DevelopmentConfig)
