"""Browse & search service: read-only aggregate view over the catalog.

Returns titles with live availability (available copies over total). Exposes no
internal barcodes or locations — this is the borrower-facing view.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session as DbSession

from ..models.base import CopyStatus
from ..models.copy import Copy
from ..models.title import Title


def _like_escape(value: str) -> str:
    """Escape LIKE metacharacters so `%` and `_` are matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@dataclass
class BrowseRow:
    id: str
    name: str
    author: str | None
    media_type: str | None
    available_count: int
    total_count: int


def search_titles(db: DbSession, q: str | None = None) -> list[BrowseRow]:
    """List titles (optionally filtered by a case-insensitive substring across
    name/author/isbn), each with live availability counts."""
    total = func.count(Copy.id)
    available = func.sum(case((Copy.status == CopyStatus.available, 1), else_=0))
    stmt = (
        select(
            Title.id,
            Title.name,
            Title.author,
            Title.media_type,
            func.coalesce(available, 0),
            func.coalesce(total, 0),
        )
        .select_from(Title)
        .outerjoin(Copy, and_(Copy.title_id == Title.id, Copy.deleted_at.is_(None)))
        .where(Title.deleted_at.is_(None))
        .group_by(Title.id)
        .order_by(func.lower(Title.name))
    )

    if q:
        needle = f"%{_like_escape(q.strip().lower())}%"
        stmt = stmt.where(
            or_(
                func.lower(Title.name).like(needle, escape="\\"),
                func.lower(func.coalesce(Title.author, "")).like(needle, escape="\\"),
                func.lower(func.coalesce(Title.isbn, "")).like(needle, escape="\\"),
            )
        )

    rows = db.execute(stmt).all()
    return [
        BrowseRow(
            id=r[0], name=r[1], author=r[2], media_type=r[3],
            available_count=int(r[4]), total_count=int(r[5]),
        )
        for r in rows
    ]
