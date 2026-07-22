"""Administrator password-reset queue router (Administrator only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..schemas.reset import IssuedTemporaryPassword, PendingResetView
from ..services import audit as audit_service
from ..services import reset as reset_service
from .deps import require_admin, require_admin_write

router = APIRouter(prefix="/admin/reset-requests", tags=["admin:reset"])


@router.get("", response_model=list[PendingResetView])
def list_requests(admin=Depends(require_admin), db: DbSession = Depends(get_db)) -> list[PendingResetView]:
    views = [
        PendingResetView(
            id=v.id, username=v.username, status=v.status, requested_at=v.requested_at
        )
        for v in reset_service.list_pending(db)
    ]
    # PII access (usernames + reset state) is itself auditable.
    audit_service.record(
        db, action="reset.queue.view", actor_id=admin.user.id,
        reason=f"viewed {len(views)} pending reset request(s)",
    )
    db.commit()
    return views


@router.post("/{request_id}/issue", response_model=IssuedTemporaryPassword)
def issue(
    request_id: str,
    admin=Depends(require_admin_write),
    db: DbSession = Depends(get_db),
) -> IssuedTemporaryPassword:
    try:
        temp_password, expires_at = reset_service.issue_temporary_password(
            db, actor_id=admin.user.id, request_id=request_id
        )
    except reset_service.RequestNotActionableError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="request not found") from exc
    db.commit()
    return IssuedTemporaryPassword(temporary_password=temp_password, expires_at=expires_at)
