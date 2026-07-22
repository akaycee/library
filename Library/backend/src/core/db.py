"""Database engine and session setup.

Uses SQLCipher for encryption at rest when a key is configured and the driver is
available; otherwise falls back to a plain local SQLite file for development and
testing only. The SQLCipher key is applied via a ``PRAGMA key`` on each new
connection and is never logged.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings


def _sqlcipher_available() -> bool:
    try:
        import sqlcipher3  # noqa: F401

        return True
    except Exception:
        return False


def _register_fk_pragma(engine) -> None:
    """Enable SQLite foreign-key enforcement on every new connection. Applies to
    both the plain-SQLite and SQLCipher engines (the packaged, encrypted
    deployment relies on FK integrity just as much as dev does)."""

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _record):  # pragma: no cover - trivial
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _build_engine():
    settings = get_settings()
    key = settings.db_key

    if key and _sqlcipher_available():
        # SQLAlchemy dialect backed by the sqlcipher3 driver.
        engine = create_engine(
            f"sqlite+pysqlcipher://:{key}@/{settings.db_path}",
            connect_args={"check_same_thread": False},
            future=True,
        )
        _register_fk_pragma(engine)
        return engine

    # Development/test fallback: plain SQLite (NOT encrypted). The packaged
    # deployment MUST provide a key and the sqlcipher driver.
    engine = create_engine(
        f"sqlite:///{settings.db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    _register_fk_pragma(engine)
    return engine


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, class_=Session)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_encrypted_at_rest() -> bool:
    """True when the active engine encrypts the database at rest."""
    settings = get_settings()
    return bool(settings.db_key) and _sqlcipher_available()


class EncryptionNotConfiguredError(RuntimeError):
    """Raised at startup when encryption at rest is required but unavailable."""


def enforce_encryption_at_rest() -> None:
    """Fail closed: when ``require_encryption`` is set, refuse to start unless the
    database is actually encrypted (key present AND SQLCipher driver available).
    Prevents silently serving PII from a plaintext SQLite file (FR-030)."""
    settings = get_settings()
    if not settings.require_encryption:
        return
    if is_encrypted_at_rest():
        return
    if not settings.db_key:
        raise EncryptionNotConfiguredError(
            "Encryption at rest is required but LIBRARY_DB_KEY is not set. "
            "Provide a key, or set LIBRARY_REQUIRE_ENCRYPTION=false for local dev."
        )
    raise EncryptionNotConfiguredError(
        "Encryption at rest is required but the SQLCipher driver is unavailable. "
        "Install the sqlcipher3 driver, or set LIBRARY_REQUIRE_ENCRYPTION=false for local dev."
    )
