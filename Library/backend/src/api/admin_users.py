"""Administrator user-management router (Administrator only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..core.password_policy import PasswordPolicyError
from ..core.username import UsernameError
from ..schemas.users import CreateUserRequest, RoleUpdate, StatusUpdate, UserAdminView
from ..services import audit as audit_service
from ..services import users as users_service
from .deps import require_admin, require_admin_write

router = APIRouter(prefix="/admin/users", tags=["admin:users"])


def _view(user) -> UserAdminView:
    return UserAdminView(
        id=user.id,
        username=user.username,
        role=user.role,
        status=user.status,
        force_password_change=user.force_password_change,
        created_at=user.created_at,
    )


@router.get("", response_model=list[UserAdminView])
def list_users(admin=Depends(require_admin), db: DbSession = Depends(get_db)) -> list[UserAdminView]:
    users = [_view(u) for u in users_service.list_users(db)]
    # Reading the full user directory (PII) is auditable.
    audit_service.record(
        db, action="user.list.view", actor_id=admin.user.id,
        reason=f"viewed {len(users)} user record(s)",
    )
    db.commit()
    return users


@router.post("", status_code=status.HTTP_201_CREATED, response_model=UserAdminView)
def create_user(
    payload: CreateUserRequest,
    admin=Depends(require_admin_write),
    db: DbSession = Depends(get_db),
) -> UserAdminView:
    try:
        user = users_service.create_user(
            db,
            actor_id=admin.user.id,
            username=payload.username,
            password=payload.password,
            role=payload.role,
        )
    except users_service.UsernameTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username unavailable") from exc
    except (UsernameError, PasswordPolicyError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return _view(user)


@router.patch("/{user_id}/role", response_model=UserAdminView)
def change_role(
    user_id: str,
    payload: RoleUpdate,
    admin=Depends(require_admin_write),
    db: DbSession = Depends(get_db),
) -> UserAdminView:
    try:
        user = users_service.change_role(
            db, actor_id=admin.user.id, user_id=user_id, new_role=payload.role
        )
    except users_service.UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found") from exc
    except users_service.LastAdministratorError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot remove the last administrator.",
        ) from exc
    db.commit()
    return _view(user)


@router.patch("/{user_id}/status", response_model=UserAdminView)
def set_status(
    user_id: str,
    payload: StatusUpdate,
    admin=Depends(require_admin_write),
    db: DbSession = Depends(get_db),
) -> UserAdminView:
    try:
        user = users_service.set_status(
            db, actor_id=admin.user.id, user_id=user_id, new_status=payload.status
        )
    except users_service.UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found") from exc
    except users_service.LastAdministratorError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot deactivate the last administrator.",
        ) from exc
    db.commit()
    return _view(user)
