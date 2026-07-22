"""Database schema creation helper.

For v1 the schema is created directly from the models. Alembic migrations wrap
this for production; ``create_all`` keeps local/dev/test setup simple.
"""

from __future__ import annotations

from .db import engine
from ..models import Base


def create_all() -> None:
    Base.metadata.create_all(bind=engine)
