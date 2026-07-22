"""Administrator user-management service.

Enforces the last-active-Administrator guard, revokes sessions on deactivation,
and writes an audit entry for every mutation.
"""

from __future__ import annotations

import secrets

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..core.password_policy import validate_password
from ..core.security import hash_password
from ..core.username import validate_username
from ..models.base import Role, UserStatus
from ..models.user import User
from . import audit
from . import sessions as session_service


class UserManagementError(Exception):
    """Base error for user management."""


class UsernameTakenError(UserManagementError):
    pass


class LastAdministratorError(UserManagementError):
    """Raised when an action would remove the last active Administrator."""


class UserNotFoundError(UserManagementError):
    pass


def _active_admin_count(db: DbSession) -> int:
    return db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == Role.administrator, User.status == UserStatus.active)
    ) or 0


def _is_last_active_admin(db: DbSession, user: User) -> bool:
    return (
        user.role == Role.administrator
        and user.status == UserStatus.active
        and _active_admin_count(db) <= 1
    )


def _ensure_admin_remains(db: DbSession) -> None:
    """Post-condition guard: after a role/status change is applied and flushed,
    verify at least one active Administrator still exists. Because SQLite
    serializes writers, this write-then-verify closes the check-then-write race
    that a bare pre-check leaves open."""
    if _active_admin_count(db) < 1:
        raise LastAdministratorError("cannot remove the last administrator")


def list_users(db: DbSession) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at)).all())


def get_user(db: DbSession, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise UserNotFoundError("user not found")
    return user


def create_user(db: DbSession, *, actor_id: str, username: str, password: str, role: Role) -> User:
    display, normalized = validate_username(username)
    validate_password(password)
    exists = db.scalar(select(User).where(User.username_normalized == normalized))
    if exists is not None:
        raise UsernameTakenError("username unavailable")
    user = User(
        username=display,
        username_normalized=normalized,
        password_hash=hash_password(password),
        role=role,
        status=UserStatus.active,
        force_password_change=True,
    )
    db.add(user)
    db.flush()
    audit.record(
        db,
        action="user.create",
        actor_id=actor_id,
        target_id=user.id,
        reason=f"created with role {role.value}",
    )
    return user


def create_borrower(
    db: DbSession, *, actor_id: str, username: str, password: str | None = None
) -> tuple[User, str | None]:
    """Create a borrower from the circulation desk. If no password is supplied a
    policy-compliant temporary one is generated and returned so staff can hand it
    to the borrower; the borrower must change it on first login.

    Returns (user, generated_password) where generated_password is None when the
    caller supplied their own password.
    """
    generated: str | None = None
    if not (password or "").strip():
        # token_urlsafe(9) yields 12 chars; the suffix guarantees a letter+digit.
        password = secrets.token_urlsafe(9) + "a1"
        generated = password
    user = create_user(
        db, actor_id=actor_id, username=username, password=password, role=Role.borrower
    )
    return user, generated


def change_role(db: DbSession, *, actor_id: str, user_id: str, new_role: Role) -> User:
    user = get_user(db, user_id)
    if user.role == new_role:
        return user
    # Demoting the last active Administrator would lock everyone out.
    if new_role != Role.administrator and _is_last_active_admin(db, user):
        raise LastAdministratorError("cannot demote the last administrator")
    old_role = user.role
    user.role = new_role
    db.flush()
    _ensure_admin_remains(db)
    audit.record(
        db,
        action="role.change",
        actor_id=actor_id,
        target_id=user.id,
        reason=f"role changed from {old_role.value} to {new_role.value}",
    )
    return user


def set_status(db: DbSession, *, actor_id: str, user_id: str, new_status: UserStatus) -> User:
    user = get_user(db, user_id)
    if user.status == new_status:
        return user
    if new_status == UserStatus.deactivated and _is_last_active_admin(db, user):
        raise LastAdministratorError("cannot deactivate the last administrator")
    user.status = new_status
    db.flush()
    _ensure_admin_remains(db)
    if new_status == UserStatus.deactivated:
        # Revoke all of the user's sessions so access ends immediately.
        session_service.revoke_all_for_user(db, user.id)
    audit.record(
        db,
        action="user.deactivate" if new_status == UserStatus.deactivated else "user.reactivate",
        actor_id=actor_id,
        target_id=user.id,
        reason=f"status set to {new_status.value}",
    )
    return user
