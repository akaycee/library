"""Application configuration and settings.

All security-relevant defaults (session lifetimes, login throttling, temp-password
expiry, password policy) live here so they are configurable per the spec.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LIBRARY_", env_file=".env", extra="ignore")

    # Database ---------------------------------------------------------------
    # Path to the local SQLite/SQLCipher database file.
    db_path: str = "library.db"
    # SQLCipher encryption key. When set (and the sqlcipher driver is available)
    # the database is encrypted at rest. Must be supplied at startup for the
    # packaged deployment; never commit or log it.
    db_key: str | None = None
    # Fail closed: require an encrypted store at startup. Defaults to True so the
    # packaged deployment cannot silently run on plaintext SQLite. Local dev and
    # the test suite opt out via LIBRARY_REQUIRE_ENCRYPTION=false.
    require_encryption: bool = True

    # Sessions ---------------------------------------------------------------
    session_cookie_name: str = "library_session"
    csrf_cookie_name: str = "library_csrf"
    session_absolute_ttl_seconds: int = 12 * 60 * 60  # 12h
    session_idle_ttl_seconds: int = 30 * 60  # 30m
    # Secure cookies require HTTPS. Disable ONLY for local http dev.
    cookie_secure: bool = True

    # Login throttling -------------------------------------------------------
    login_max_failures: int = 5
    login_lock_seconds: int = 15 * 60  # 15m
    login_failure_window_seconds: int = 15 * 60

    # Temporary password -----------------------------------------------------
    temp_password_ttl_seconds: int = 24 * 60 * 60  # 24h

    # Password policy --------------------------------------------------------
    password_min_length: int = 8

    # Username policy --------------------------------------------------------
    username_max_length: int = 32

    # Location policy --------------------------------------------------------
    location_max_depth: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
