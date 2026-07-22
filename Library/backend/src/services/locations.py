"""Location tree service: build, create, rename, move, delete.

Uses an adjacency list. Cycle prevention, sibling-name uniqueness, and a
configurable depth cap are enforced here; every mutation is audited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..core.config import get_settings
from ..core.locations_name import validate_location_name
from ..models.location import Location
from . import audit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LocationError(Exception):
    pass


class LocationNotFoundError(LocationError):
    pass


class DuplicateSiblingError(LocationError):
    pass


class CycleError(LocationError):
    pass


class NotEmptyError(LocationError):
    pass


class MaxDepthError(LocationError):
    pass


# --- Item hook: counts catalog copies assigned to a location --------------------
def item_count(db: DbSession, location_id: str) -> int:
    """Number of catalog copies assigned to a location. Implemented by the catalog
    feature; a location holding copies cannot be deleted."""
    from ..models.copy import Copy

    return (
        db.scalar(
            select(func.count())
            .select_from(Copy)
            .where(Copy.location_id == location_id, Copy.deleted_at.is_(None))
        )
        or 0
    )


# --- Tree view ----------------------------------------------------------------
@dataclass
class TreeNode:
    id: str
    name: str
    type_label: str | None
    parent_id: str | None
    children: list["TreeNode"] = field(default_factory=list)


def _load_all(db: DbSession) -> list[Location]:
    return list(db.scalars(select(Location).where(Location.deleted_at.is_(None))).all())


def list_tree(db: DbSession) -> list[TreeNode]:
    rows = _load_all(db)
    nodes: dict[str, TreeNode] = {
        r.id: TreeNode(id=r.id, name=r.name, type_label=r.type_label, parent_id=r.parent_id)
        for r in rows
    }
    roots: list[TreeNode] = []
    for r in rows:
        node = nodes[r.id]
        if r.parent_id and r.parent_id in nodes:
            nodes[r.parent_id].children.append(node)
        else:
            roots.append(node)

    def sort_rec(items: list[TreeNode]) -> None:
        items.sort(key=lambda n: n.name.casefold())
        for it in items:
            sort_rec(it.children)

    sort_rec(roots)
    return roots


# --- Helpers ------------------------------------------------------------------
def _get(db: DbSession, location_id: str) -> Location:
    loc = db.get(Location, location_id)
    if loc is None or loc.deleted_at is not None:
        raise LocationNotFoundError("location not found")
    return loc


def _sibling_exists(
    db: DbSession, *, parent_id: str | None, name_normalized: str, exclude_id: str | None = None
) -> bool:
    stmt = select(Location).where(
        Location.parent_id == parent_id,
        Location.name_normalized == name_normalized,
        Location.deleted_at.is_(None),
    )
    if exclude_id is not None:
        stmt = stmt.where(Location.id != exclude_id)
    return db.scalar(stmt) is not None


def _depth(db: DbSession, location: Location) -> int:
    """Number of ancestors (root = 0)."""
    depth = 0
    current = location
    seen: set[str] = set()
    while current.parent_id and current.parent_id not in seen:
        seen.add(current.id)
        parent = db.get(Location, current.parent_id)
        if parent is None:
            break
        depth += 1
        current = parent
    return depth


def _subtree_height(db: DbSession, location_id: str) -> int:
    """Height of the subtree rooted at location_id (leaf = 0)."""
    children = db.scalars(
        select(Location).where(
            Location.parent_id == location_id, Location.deleted_at.is_(None)
        )
    ).all()
    if not children:
        return 0
    return 1 + max(_subtree_height(db, c.id) for c in children)


def _is_self_or_descendant(db: DbSession, *, node_id: str, candidate_id: str) -> bool:
    """True if candidate_id is node_id or a descendant of node_id."""
    if candidate_id == node_id:
        return True
    current = db.get(Location, candidate_id)
    seen: set[str] = set()
    while current and current.parent_id and current.parent_id not in seen:
        if current.parent_id == node_id:
            return True
        seen.add(current.id)
        current = db.get(Location, current.parent_id)
    return False


# --- Mutations ----------------------------------------------------------------
def create(
    db: DbSession,
    *,
    actor_id: str,
    name: str,
    type_label: str | None,
    parent_id: str | None,
) -> Location:
    display, normalized = validate_location_name(name)
    settings = get_settings()

    if parent_id is not None:
        parent = _get(db, parent_id)
        if _depth(db, parent) + 1 > settings.location_max_depth - 1:
            raise MaxDepthError("maximum nesting depth exceeded")

    if _sibling_exists(db, parent_id=parent_id, name_normalized=normalized):
        raise DuplicateSiblingError("a location with that name already exists here")

    loc = Location(
        name=display,
        name_normalized=normalized,
        type_label=(type_label or None),
        parent_id=parent_id,
        created_by=actor_id,
    )
    db.add(loc)
    db.flush()
    audit.record(
        db, action="location.create", actor_id=actor_id, entity_type="location", entity_id=loc.id,
        reason=f"created location '{display}'",
        detail=audit.snapshot_detail({"name": display, "type_label": loc.type_label, "parent_id": parent_id}),
    )
    return loc


def rename(
    db: DbSession, *, actor_id: str, location_id: str, name: str | None, type_label: str | None,
    type_label_provided: bool,
) -> Location:
    loc = _get(db, location_id)
    before = {"name": loc.name, "type_label": loc.type_label}
    if name is not None:
        display, normalized = validate_location_name(name)
        if normalized != loc.name_normalized and _sibling_exists(
            db, parent_id=loc.parent_id, name_normalized=normalized, exclude_id=loc.id
        ):
            raise DuplicateSiblingError("a location with that name already exists here")
        loc.name = display
        loc.name_normalized = normalized
    if type_label_provided:
        loc.type_label = type_label or None
    after = {"name": loc.name, "type_label": loc.type_label}
    db.flush()
    audit.record(
        db, action="location.rename", actor_id=actor_id, entity_type="location", entity_id=loc.id,
        reason=f"updated location '{loc.name}'", detail=audit.changes_detail(before, after),
    )
    return loc


def move(db: DbSession, *, actor_id: str, location_id: str, new_parent_id: str | None) -> Location:
    loc = _get(db, location_id)
    settings = get_settings()
    old_parent_id = loc.parent_id

    if new_parent_id is not None:
        _get(db, new_parent_id)  # 404 if missing
        if _is_self_or_descendant(db, node_id=loc.id, candidate_id=new_parent_id):
            raise CycleError("cannot move a location under itself")
        new_parent = db.get(Location, new_parent_id)
        new_depth = _depth(db, new_parent) + 1 + _subtree_height(db, loc.id)
        if new_depth > settings.location_max_depth - 1:
            raise MaxDepthError("maximum nesting depth exceeded")

    if _sibling_exists(
        db, parent_id=new_parent_id, name_normalized=loc.name_normalized, exclude_id=loc.id
    ):
        raise DuplicateSiblingError("a location with that name already exists at the destination")

    loc.parent_id = new_parent_id
    db.flush()
    audit.record(
        db, action="location.move", actor_id=actor_id, entity_type="location", entity_id=loc.id,
        reason=f"moved location '{loc.name}'",
        detail=audit.changes_detail({"parent_id": old_parent_id}, {"parent_id": new_parent_id}),
    )
    return loc


def delete(db: DbSession, *, actor_id: str, location_id: str) -> None:
    loc = _get(db, location_id)
    child_count = db.scalar(
        select(func.count())
        .select_from(Location)
        .where(Location.parent_id == loc.id, Location.deleted_at.is_(None))
    ) or 0
    if child_count > 0:
        raise NotEmptyError("this location has sub-locations")
    if item_count(db, loc.id) > 0:
        raise NotEmptyError("this location has items")
    name = loc.name
    # Soft delete: retain the row for history; hidden from all live views.
    loc.deleted_at = _utcnow()
    db.flush()
    audit.record(
        db, action="location.delete", actor_id=actor_id, entity_type="location", entity_id=location_id,
        reason=f"deleted location '{name}'",
    )
