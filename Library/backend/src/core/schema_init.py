"""Create the database schema (tables). Run once before first use:

    python -m src.core.schema_init
"""

from __future__ import annotations

from .schema import create_all

if __name__ == "__main__":  # pragma: no cover
    create_all()
    print("Database schema created.")
