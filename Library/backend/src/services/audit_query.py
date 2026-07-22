"""Audit read service (F7): a query layer over the append-only audit log.

Read-only. Resolves actor/target ids to usernames and supports filtering by
action, by actor/target username (contains), and by a from/to date range, with
newest-first ordering and limit/offset paging.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session as DbSession

from ..models.audit import AuditLogEntry
from ..models.user import User

MAX_LIMIT = 200
DEFAULT_LIMIT = 50


@dataclass
class AuditEntryRow:
    id: str
    action: str
    actor: str | None
    target: str | None
    entity_type: str | None
    entity_id: str | None
    reason: str | None
    detail: str | None
    created_at: datetime


def action_types(db: DbSession) -> list[str]:
    return list(
        db.scalars(select(AuditLogEntry.action).distinct().order_by(AuditLogEntry.action)).all()
    )


def _matching_user_ids(db: DbSession, q: str) -> list[str]:
    like = f"%{q.strip().casefold()}%"
    return list(
        db.scalars(select(User.id).where(User.username_normalized.like(like))).all()
    )


def list_entries(
    db: DbSession,
    *,
    action: str | None = None,
    q: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> list[AuditEntryRow]:
    limit = max(1, min(limit, MAX_LIMIT))
    offset = max(0, offset)

    stmt = select(AuditLogEntry)
    if action:
        stmt = stmt.where(AuditLogEntry.action == action)
    if q and q.strip():
        ids = _matching_user_ids(db, q)
        if not ids:
            return []  # no user matches -> no actor/target can match
        stmt = stmt.where(
            or_(AuditLogEntry.actor_id.in_(ids), AuditLogEntry.target_id.in_(ids))
        )
    if start is not None:
        stmt = stmt.where(AuditLogEntry.created_at >= start)
    if end is not None:
        stmt = stmt.where(AuditLogEntry.created_at <= end)

    stmt = stmt.order_by(AuditLogEntry.created_at.desc(), AuditLogEntry.id.desc())
    stmt = stmt.limit(limit).offset(offset)
    entries = list(db.scalars(stmt).all())

    # Resolve actor/target ids to usernames in one round-trip.
    ids: set[str] = set()
    for e in entries:
        if e.actor_id:
            ids.add(e.actor_id)
        if e.target_id:
            ids.add(e.target_id)
    names: dict[str, str] = {}
    if ids:
        for uid, uname in db.execute(
            select(User.id, User.username).where(User.id.in_(ids))
        ).all():
            names[uid] = uname

    return [
        AuditEntryRow(
            id=e.id,
            action=e.action,
            actor=names.get(e.actor_id) if e.actor_id else None,
            target=names.get(e.target_id) if e.target_id else None,
            entity_type=e.entity_type,
            entity_id=e.entity_id,
            reason=e.reason,
            detail=e.detail,
            created_at=e.created_at,
        )
        for e in entries
    ]


def count_entries(db: DbSession) -> int:
    return db.scalar(select(func.count()).select_from(AuditLogEntry)) or 0
