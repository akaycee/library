"""Audit trail router (F7): staff-only, read-only views over the audit log."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..services import audit_query as svc
from .deps import require_staff

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEntryView(BaseModel):
    id: str
    action: str
    actor: str | None
    target: str | None
    entity_type: str | None
    entity_id: str | None
    reason: str | None
    detail: str | None
    created_at: datetime


@router.get("/actions", response_model=list[str])
def list_actions(_staff=Depends(require_staff), db: DbSession = Depends(get_db)) -> list[str]:
    return svc.action_types(db)


@router.get("", response_model=list[AuditEntryView])
def list_audit(
    action: str | None = None,
    q: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(default=svc.DEFAULT_LIMIT, ge=1, le=svc.MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    _staff=Depends(require_staff),
    db: DbSession = Depends(get_db),
) -> list[AuditEntryView]:
    rows = svc.list_entries(
        db, action=action, q=q, start=start, end=end, limit=limit, offset=offset
    )
    return [
        AuditEntryView(
            id=r.id,
            action=r.action,
            actor=r.actor,
            target=r.target,
            entity_type=r.entity_type,
            entity_id=r.entity_id,
            reason=r.reason,
            detail=r.detail,
            created_at=r.created_at,
        )
        for r in rows
    ]
