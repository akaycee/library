"""Catalog service: Titles and their physical Copies.

Barcodes are unique sequential accession numbers (auto or manual-if-unique).
Status/delete guards protect active loans (checked_out) and prevent orphans.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from ..models.base import CopyStatus
from ..models.copy import Copy
from ..models.location import Location
from ..models.title import Title
from . import audit

_BARCODE_PREFIX = "LIB-"
_BARCODE_WIDTH = 6
_MAX_RETRIES = 5


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CatalogError(Exception):
    pass


class TitleNotFoundError(CatalogError):
    pass


class CopyNotFoundError(CatalogError):
    pass


class LocationNotFoundError(CatalogError):
    pass


class DuplicateBarcodeError(CatalogError):
    pass


class TitleHasCopiesError(CatalogError):
    pass


class CopyCheckedOutError(CatalogError):
    pass


class InvalidStatusError(CatalogError):
    pass


# --- Helpers ------------------------------------------------------------------
def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    v = value.strip()
    return v or None


def _require_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        raise CatalogError("name must not be empty")
    return n


def _get_title(db: DbSession, title_id: str) -> Title:
    t = db.get(Title, title_id)
    if t is None or t.deleted_at is not None:
        raise TitleNotFoundError("title not found")
    return t


def _get_copy(db: DbSession, copy_id: str) -> Copy:
    c = db.get(Copy, copy_id)
    if c is None or c.deleted_at is not None:
        raise CopyNotFoundError("copy not found")
    return c


def _require_location(db: DbSession, location_id: str) -> Location:
    loc = db.get(Location, location_id)
    if loc is None or loc.deleted_at is not None:
        raise LocationNotFoundError("location not found")
    return loc


def location_path(db: DbSession, location_id: str | None) -> str:
    if not location_id:
        return ""
    names: list[str] = []
    seen: set[str] = set()
    current = db.get(Location, location_id)
    while current and current.id not in seen:
        names.append(current.name)
        seen.add(current.id)
        current = db.get(Location, current.parent_id) if current.parent_id else None
    return " / ".join(reversed(names))


def _next_barcode(db: DbSession) -> str:
    """Next sequential accession number. Considers ONLY auto-format barcodes
    (``LIB-`` followed by digits) so a manual barcode like ``LIB-ZZZ`` can never
    poison future allocation."""
    candidates = db.scalars(
        select(Copy.barcode).where(Copy.barcode.like(f"{_BARCODE_PREFIX}%"))
    ).all()
    highest = 0
    for bc in candidates:
        suffix = bc[len(_BARCODE_PREFIX):]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"{_BARCODE_PREFIX}{highest + 1:0{_BARCODE_WIDTH}d}"


# --- Views --------------------------------------------------------------------
@dataclass
class CopyRow:
    id: str
    barcode: str
    location_id: str
    location_path: str
    status: str
    condition: str | None


def copy_row(db: DbSession, c: Copy) -> CopyRow:
    return CopyRow(
        id=c.id,
        barcode=c.barcode,
        location_id=c.location_id,
        location_path=location_path(db, c.location_id),
        status=c.status.value,
        condition=c.condition,
    )


# --- Titles -------------------------------------------------------------------
def create_title(
    db: DbSession, *, actor_id: str, name: str, author: str | None, isbn: str | None,
    media_type: str | None,
) -> Title:
    title = Title(
        name=_require_name(name),
        author=_clean(author),
        isbn=_clean(isbn),
        media_type=_clean(media_type),
        created_by=actor_id,
    )
    db.add(title)
    db.flush()
    audit.record(
        db, action="title.create", actor_id=actor_id, entity_type="title", entity_id=title.id,
        reason=f"created title '{title.name}'",
        detail=audit.snapshot_detail(
            {"name": title.name, "author": title.author, "isbn": title.isbn, "media_type": title.media_type}
        ),
    )
    return title


def list_titles(db: DbSession) -> list[tuple[Title, int]]:
    titles = db.scalars(
        select(Title).where(Title.deleted_at.is_(None)).order_by(Title.name)
    ).all()
    result: list[tuple[Title, int]] = []
    for t in titles:
        count = db.scalar(
            select(func.count())
            .select_from(Copy)
            .where(Copy.title_id == t.id, Copy.deleted_at.is_(None))
        ) or 0
        result.append((t, count))
    return result


def get_title(db: DbSession, title_id: str) -> tuple[Title, list[Copy]]:
    title = _get_title(db, title_id)
    copies = db.scalars(
        select(Copy)
        .where(Copy.title_id == title.id, Copy.deleted_at.is_(None))
        .order_by(Copy.barcode)
    ).all()
    return title, list(copies)


def update_title(
    db: DbSession, *, actor_id: str, title_id: str, name: str | None, author: str | None,
    isbn: str | None, media_type: str | None, fields_set: set[str],
) -> Title:
    title = _get_title(db, title_id)
    before = {"name": title.name, "author": title.author, "isbn": title.isbn, "media_type": title.media_type}
    if "name" in fields_set and name is not None:
        title.name = _require_name(name)
    if "author" in fields_set:
        title.author = _clean(author)
    if "isbn" in fields_set:
        title.isbn = _clean(isbn)
    if "media_type" in fields_set:
        title.media_type = _clean(media_type)
    after = {"name": title.name, "author": title.author, "isbn": title.isbn, "media_type": title.media_type}
    db.flush()
    audit.record(
        db, action="title.update", actor_id=actor_id, entity_type="title", entity_id=title.id,
        reason=f"updated title '{title.name}'", detail=audit.changes_detail(before, after),
    )
    return title


def delete_title(db: DbSession, *, actor_id: str, title_id: str) -> None:
    title = _get_title(db, title_id)
    count = db.scalar(
        select(func.count())
        .select_from(Copy)
        .where(Copy.title_id == title.id, Copy.deleted_at.is_(None))
    ) or 0
    if count > 0:
        raise TitleHasCopiesError("this title still has copies")
    name = title.name
    # Soft delete: retain the row (and its history/loans) but hide it from views.
    title.deleted_at = _utcnow()
    db.flush()
    audit.record(db, action="title.delete", actor_id=actor_id, entity_type="title", entity_id=title_id, reason=f"deleted title '{name}'")


# --- Copies -------------------------------------------------------------------
def add_copy(
    db: DbSession, *, actor_id: str, title_id: str, location_id: str, barcode: str | None,
    condition: str | None,
) -> Copy:
    _get_title(db, title_id)
    _require_location(db, location_id)

    manual = _clean(barcode)
    if manual is not None:
        if db.scalar(select(Copy).where(Copy.barcode == manual)) is not None:
            raise DuplicateBarcodeError("that barcode is already in use")
        copy = _insert_copy(db, title_id, location_id, manual, condition, actor_id)
        return copy

    # Auto-generate with retry on the unique constraint.
    last_error: Exception | None = None
    for _ in range(_MAX_RETRIES):
        candidate = _next_barcode(db)
        try:
            with db.begin_nested():
                copy = Copy(
                    title_id=title_id,
                    barcode=candidate,
                    location_id=location_id,
                    status=CopyStatus.available,
                    condition=_clean(condition),
                    created_by=actor_id,
                )
                db.add(copy)
                db.flush()
            audit.record(db, action="copy.create", actor_id=actor_id, entity_type="copy", entity_id=copy.id, reason=f"added copy {candidate}", detail=audit.snapshot_detail({"barcode": candidate, "location_id": location_id}))
            return copy
        except IntegrityError as exc:  # pragma: no cover - concurrency backstop
            last_error = exc
    raise CatalogError("could not allocate a unique barcode") from last_error


def _insert_copy(db, title_id, location_id, barcode, condition, actor_id) -> Copy:
    copy = Copy(
        title_id=title_id,
        barcode=barcode,
        location_id=location_id,
        status=CopyStatus.available,
        condition=_clean(condition),
        created_by=actor_id,
    )
    db.add(copy)
    db.flush()
    audit.record(db, action="copy.create", actor_id=actor_id, entity_type="copy", entity_id=copy.id, reason=f"added copy {barcode}", detail=audit.snapshot_detail({"barcode": barcode, "location_id": location_id}))
    return copy


def move_copy(
    db: DbSession, *, actor_id: str, copy_id: str, location_id: str | None, condition: str | None,
    fields_set: set[str],
) -> Copy:
    copy = _get_copy(db, copy_id)
    before = {"location_id": copy.location_id, "condition": copy.condition}
    if "location_id" in fields_set and location_id is not None:
        _require_location(db, location_id)
        copy.location_id = location_id
    if "condition" in fields_set:
        copy.condition = _clean(condition)
    after = {"location_id": copy.location_id, "condition": copy.condition}
    db.flush()
    audit.record(db, action="copy.move", actor_id=actor_id, entity_type="copy", entity_id=copy.id, reason=f"updated copy {copy.barcode}", detail=audit.changes_detail(before, after))
    return copy


_MANUAL_STATUSES = {CopyStatus.available, CopyStatus.lost, CopyStatus.withdrawn}


def set_copy_status(db: DbSession, *, actor_id: str, copy_id: str, new_status: CopyStatus) -> Copy:
    copy = _get_copy(db, copy_id)
    if new_status == CopyStatus.checked_out:
        raise InvalidStatusError("checked_out is managed by borrowing, not set manually")
    if copy.status == CopyStatus.checked_out:
        raise CopyCheckedOutError("this copy is checked out; resolve the loan first")
    old_status = copy.status
    copy.status = new_status
    db.flush()
    audit.record(db, action="copy.status", actor_id=actor_id, entity_type="copy", entity_id=copy.id, reason=f"copy {copy.barcode} -> {new_status.value}", detail=audit.changes_detail({"status": old_status.value}, {"status": new_status.value}))
    return copy


def delete_copy(db: DbSession, *, actor_id: str, copy_id: str) -> None:
    copy = _get_copy(db, copy_id)
    if copy.status == CopyStatus.checked_out:
        raise CopyCheckedOutError("this copy is checked out and cannot be deleted")
    barcode = copy.barcode
    # Soft delete: keep the row so returned-loan history/FKs stay intact.
    copy.deleted_at = _utcnow()
    db.flush()
    audit.record(db, action="copy.delete", actor_id=actor_id, entity_type="copy", entity_id=copy_id, reason=f"deleted copy {barcode}")
