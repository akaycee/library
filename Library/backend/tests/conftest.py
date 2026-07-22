"""Test fixtures: isolated in-memory-ish DB and a TestClient with dependency
overrides. Cookies are non-Secure in tests so the TestClient sends them over HTTP.
"""

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure dev/test config (non-Secure cookies, no encryption key) before imports.
os.environ.setdefault("LIBRARY_COOKIE_SECURE", "false")
os.environ.setdefault("LIBRARY_REQUIRE_ENCRYPTION", "false")

from src.api.deps import get_current  # noqa: E402
from src.core.db import get_db  # noqa: E402
from src.main import app  # noqa: E402
from src.models import Base  # noqa: E402


@pytest.fixture()
def db_session():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False}, future=True
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        os.unlink(path)


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
