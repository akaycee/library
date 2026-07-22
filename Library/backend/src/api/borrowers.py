"""Borrower quick-create router (F6 desk enhancement).

Lets staff (Librarians + Administrators) create a borrower account from the
circulation desk when the borrower isn't found. The password may be supplied by
the librarian or auto-generated; a generated password is returned once so it can
be handed to the borrower, who must change it on first login.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..core.password_policy import PasswordPolicyError
from ..core.username import UsernameError
from ..models.base import Role, UserStatus
from ..services import users as users_service
from .deps import require_staff_write

router = APIRouter(prefix="/borrowers", tags=["borrowers"])


class CreateBorrowerRequest(BaseModel):
    username: str = Field(max_length=64)
    # Optional: when omitted/blank, a temporary password is generated server-side.
    password: str | None = Field(default=None, max_length=256)


class CreatedBorrowerView(BaseModel):
    id: str
    username: str
    role: Role
    status: UserStatus
    created_at: datetime
    # Present only when the server generated the password.
    temporary_password: str | None = None


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreatedBorrowerView)
def create_borrower(
    payload: CreateBorrowerRequest,
    staff=Depends(require_staff_write),
    db: DbSession = Depends(get_db),
) -> CreatedBorrowerView:
    try:
        user, generated = users_service.create_borrower(
            db, actor_id=staff.user.id, username=payload.username, password=payload.password
        )
    except users_service.UsernameTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username unavailable") from exc
    except (UsernameError, PasswordPolicyError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return CreatedBorrowerView(
        id=user.id,
        username=user.username,
        role=user.role,
        status=user.status,
        created_at=user.created_at,
        temporary_password=generated,
    )
