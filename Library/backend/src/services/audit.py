"""Audit logging service (append-only)."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session as DbSession

from ..models.audit import AuditLogEntry


def record(
    db: DbSession,
    *,
    action: str,
    actor_id: str | None = None,
    target_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    reason: str | None = None,
    detail: str | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        action=action,
        actor_id=actor_id,
        target_id=target_id,
        entity_type=entity_type,
        entity_id=entity_id,
        reason=reason,
        detail=detail,
    )
    db.add(entry)
    return entry


def changes_detail(before: dict[str, Any], after: dict[str, Any]) -> str | None:
    """Serialize a compact {field: {from, to}} map of changed fields to JSON, so
    an update can be precisely reconstructed. Returns None when nothing changed."""
    diff: dict[str, dict[str, Any]] = {}
    for key in sorted(set(before) | set(after)):
        old = before.get(key)
        new = after.get(key)
        if old != new:
            diff[key] = {"from": old, "to": new}
    if not diff:
        return None
    return json.dumps({"changes": diff}, default=str)


def snapshot_detail(values: dict[str, Any]) -> str:
    """Serialize a full snapshot of an entity's fields to JSON (for create)."""
    return json.dumps({"values": values}, default=str)
