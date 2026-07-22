"""Authentication and registration service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..core.password_policy import validate_password
from ..core.security import hash_password, verify_password
from ..core.username import validate_username
from ..models.base import Role, UserStatus
from ..models.user import User
from . import audit
from .throttle import login_throttle


class AuthError(Exception):
    """Base authentication error."""


class UsernameTakenError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    """Raised for any failed login (invalid, unknown, or locked) so callers can
    return an indistinguishable response."""


def _get_by_normalized(db: DbSession, username_normalized: str) -> User | None:
    return db.scalar(select(User).where(User.username_normalized == username_normalized))


def register_borrower(db: DbSession, *, username: str, password: str) -> User:
    """Self-register a Borrower. Elevated roles cannot be self-registered."""
    display, normalized = validate_username(username)
    validate_password(password)
    if _get_by_normalized(db, normalized) is not None:
        raise UsernameTakenError("username unavailable")
    user = User(
        username=display,
        username_normalized=normalized,
        password_hash=hash_password(password),
        role=Role.borrower,
        status=UserStatus.active,
        force_password_change=False,
    )
    db.add(user)
    db.flush()
    audit.record(db, action="user.register", target_id=user.id, reason="borrower self-registration")
    return user


@dataclass
class AuthenticatedUser:
    user: User


def authenticate(db: DbSession, *, username: str, password: str, client: str) -> User:
    """Authenticate with a normal password. Raises InvalidCredentialsError for
    invalid credentials, unknown usernames, AND locked accounts alike."""
    try:
        _display, normalized = validate_username(username)
    except ValueError as exc:  # invalid username format -> indistinguishable failure
        raise InvalidCredentialsError("invalid credentials") from exc

    if login_throttle.is_locked(normalized, client):
        raise InvalidCredentialsError("invalid credentials")

    user = _get_by_normalized(db, normalized)
    ok = bool(user) and user.status == UserStatus.active and verify_password(password, user.password_hash)
    if not ok:
        login_throttle.record_failure(normalized, client)
        raise InvalidCredentialsError("invalid credentials")

    login_throttle.reset(normalized, client)
    return user


def set_new_password(db: DbSession, *, user: User, new_password: str) -> None:
    """Set a new password, clear the force-change flag, and audit. Caller is
    responsible for validating authorization and rotating sessions."""
    validate_password(new_password)
    user.password_hash = hash_password(new_password)
    user.force_password_change = False
    db.flush()
    audit.record(db, action="password.change", actor_id=user.id, target_id=user.id, reason="password changed")
