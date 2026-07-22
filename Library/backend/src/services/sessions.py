"""Session lifecycle: create, resolve, rotate, and revoke server-side sessions.

The cookie carries only an opaque token; the server stores its SHA-256 hash.
Sessions have absolute expiry and idle timeout and are rejected when revoked,
expired, idle-timed-out, or when their user is deactivated.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from ..core.config import get_settings
from ..core.security import generate_token, hash_token
from ..models.base import SessionKind, UserStatus
from ..models.session import Session as SessionModel
from ..models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware (SQLite may return naive UTC)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class IssuedSession:
    """The raw tokens to hand to the client (never stored in raw form)."""

    session_token: str
    csrf_token: str
    kind: SessionKind


def create_session(db: DbSession, user: User, kind: SessionKind = SessionKind.full) -> IssuedSession:
    settings = get_settings()
    token = generate_token()
    csrf = generate_token(16)
    now = _utcnow()
    model = SessionModel(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_token=csrf,
        kind=kind,
        created_at=now,
        expires_at=now + timedelta(seconds=settings.session_absolute_ttl_seconds),
        last_seen_at=now,
    )
    db.add(model)
    return IssuedSession(session_token=token, csrf_token=csrf, kind=kind)


def revoke_session_by_token(db: DbSession, token: str) -> None:
    model = db.scalar(select(SessionModel).where(SessionModel.token_hash == hash_token(token)))
    if model and model.revoked_at is None:
        model.revoked_at = _utcnow()


def revoke_all_for_user(db: DbSession, user_id: str) -> None:
    sessions = db.scalars(
        select(SessionModel).where(
            SessionModel.user_id == user_id, SessionModel.revoked_at.is_(None)
        )
    ).all()
    for s in sessions:
        s.revoked_at = _utcnow()


@dataclass
class ResolvedSession:
    session: SessionModel
    user: User


def resolve_session(db: DbSession, token: str | None) -> ResolvedSession | None:
    """Return the active session + user, or None if invalid. Enforces expiry,
    idle timeout, revocation, and user status. Updates last_seen on success."""
    if not token:
        return None
    settings = get_settings()
    model = db.scalar(select(SessionModel).where(SessionModel.token_hash == hash_token(token)))
    if not model or model.revoked_at is not None:
        return None
    now = _utcnow()
    if now >= _aware(model.expires_at):
        return None
    idle_deadline = _aware(model.last_seen_at) + timedelta(seconds=settings.session_idle_ttl_seconds)
    if now >= idle_deadline:
        model.revoked_at = now
        return None
    user = db.get(User, model.user_id)
    if not user or user.status != UserStatus.active:
        return None
    model.last_seen_at = now
    return ResolvedSession(session=model, user=user)
