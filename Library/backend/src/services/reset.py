"""Email-free password-reset service.

Flow: user submits a request (no enumeration) -> admin issues a one-time
temporary password -> user logs in with it (atomically consumed) into a
restricted session -> user sets a new password (completes the reset, revokes
other sessions).
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from ..core.config import get_settings
from ..core.security import hash_password, hash_token, verify_password
from ..core.username import validate_username
from ..models.base import ResetStatus, UserStatus
from ..models.reset import PasswordResetRequest, TemporaryPasswordGrant
from ..models.user import User
from . import audit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class ResetError(Exception):
    pass


class RateLimitedError(ResetError):
    pass


class InvalidTemporaryPasswordError(ResetError):
    pass


class RequestNotActionableError(ResetError):
    pass


# --- Simple per-client submission rate limiter (in-memory, single process) ----
class _SubmitLimiter:
    def __init__(self, max_per_window: int = 5, window_seconds: int = 600) -> None:
        self._lock = threading.Lock()
        self._hits: dict[str, list[float]] = {}
        self.max = max_per_window
        self.window = window_seconds

    def check_and_record(self, client: str) -> bool:
        now = time.time()
        with self._lock:
            hits = [t for t in self._hits.get(client, []) if now - t < self.window]
            if len(hits) >= self.max:
                self._hits[client] = hits
                return False
            hits.append(now)
            self._hits[client] = hits
            return True


submit_limiter = _SubmitLimiter()


def _get_active_user(db: DbSession, username: str) -> User | None:
    try:
        _display, normalized = validate_username(username)
    except ValueError:
        return None
    user = db.scalar(select(User).where(User.username_normalized == normalized))
    if user and user.status == UserStatus.active:
        return user
    return None


def submit_request(db: DbSession, *, username: str, client: str) -> None:
    """Queue a reset request. Always returns nothing (identical public response).

    Rate-limited per client. Creates an actionable item only for a resolved
    active user, consolidating a duplicate pending request.
    """
    if not submit_limiter.check_and_record(client):
        raise RateLimitedError("too many requests")

    user = _get_active_user(db, username)
    if user is None:
        return  # no enumeration: identical response whether or not user exists

    settings = get_settings()
    existing = db.scalar(
        select(PasswordResetRequest).where(
            PasswordResetRequest.user_id == user.id,
            PasswordResetRequest.status == ResetStatus.pending,
        )
    )
    if existing is not None:
        # Consolidate: refresh the timestamp/expiry rather than create a new row.
        existing.requested_at = _utcnow()
        existing.expires_at = _utcnow() + timedelta(seconds=settings.temp_password_ttl_seconds)
        return

    req = PasswordResetRequest(
        user_id=user.id,
        status=ResetStatus.pending,
        requested_at=_utcnow(),
        expires_at=_utcnow() + timedelta(seconds=settings.temp_password_ttl_seconds),
    )
    db.add(req)
    db.flush()
    audit.record(db, action="reset.request", target_id=user.id, reason="password reset requested")


@dataclass
class PendingRequestView:
    id: str
    username: str
    status: str
    requested_at: datetime


def list_pending(db: DbSession) -> list[PendingRequestView]:
    rows = db.scalars(
        select(PasswordResetRequest)
        .where(PasswordResetRequest.status.in_([ResetStatus.pending, ResetStatus.issued]))
        .order_by(PasswordResetRequest.requested_at)
    ).all()
    views: list[PendingRequestView] = []
    for r in rows:
        user = db.get(User, r.user_id)
        views.append(
            PendingRequestView(
                id=r.id,
                username=user.username if user else "(unknown)",
                status=r.status.value,
                requested_at=r.requested_at,
            )
        )
    return views


def issue_temporary_password(db: DbSession, *, actor_id: str, request_id: str) -> tuple[str, datetime]:
    """Issue a one-time temporary password for a pending/issued request."""
    req = db.get(PasswordResetRequest, request_id)
    if req is None or req.status not in (ResetStatus.pending, ResetStatus.issued):
        raise RequestNotActionableError("request not actionable")

    settings = get_settings()
    # Invalidate any earlier, still-unconsumed grants for this user so a reissue
    # supersedes older temporary passwords (they must not remain usable).
    now = _utcnow()
    db.execute(
        update(TemporaryPasswordGrant)
        .where(
            TemporaryPasswordGrant.user_id == req.user_id,
            TemporaryPasswordGrant.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    # Generate a temp password that satisfies the password policy.
    temp_password = secrets.token_urlsafe(9) + "1a"
    expires_at = now + timedelta(seconds=settings.temp_password_ttl_seconds)
    grant = TemporaryPasswordGrant(
        user_id=req.user_id,
        request_id=req.id,
        temp_hash=hash_password(temp_password),
        expires_at=expires_at,
    )
    db.add(grant)
    req.status = ResetStatus.issued
    req.issued_at = now
    db.flush()
    audit.record(
        db,
        action="reset.issue",
        actor_id=actor_id,
        target_id=req.user_id,
        reason="temporary password issued",
    )
    return temp_password, expires_at


def consume_temporary_login(db: DbSession, *, username: str, temporary_password: str) -> User:
    """Verify a temporary password and atomically consume the grant. Returns the
    user on success; raises InvalidTemporaryPasswordError otherwise (indistinguishable)."""
    user = _get_active_user(db, username)
    if user is None:
        raise InvalidTemporaryPasswordError("invalid temporary password")

    now = _utcnow()
    grant = db.scalar(
        select(TemporaryPasswordGrant)
        .join(
            PasswordResetRequest,
            PasswordResetRequest.id == TemporaryPasswordGrant.request_id,
        )
        .where(
            TemporaryPasswordGrant.user_id == user.id,
            TemporaryPasswordGrant.consumed_at.is_(None),
            # Only a grant whose request is still issued (not completed/expired/
            # cancelled) is valid — a superseded/finished reset must not log in.
            PasswordResetRequest.status == ResetStatus.issued,
        )
        .order_by(TemporaryPasswordGrant.expires_at.desc())
    )
    if grant is None or now >= _aware(grant.expires_at):
        raise InvalidTemporaryPasswordError("invalid temporary password")
    if not verify_password(temporary_password, grant.temp_hash):
        raise InvalidTemporaryPasswordError("invalid temporary password")

    # Atomically consume: only succeed if this grant is still unconsumed. Guards
    # against a select-then-update race where two logins race on one grant.
    result = db.execute(
        update(TemporaryPasswordGrant)
        .where(
            TemporaryPasswordGrant.id == grant.id,
            TemporaryPasswordGrant.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )
    if result.rowcount != 1:
        raise InvalidTemporaryPasswordError("invalid temporary password")
    db.flush()
    return user


def complete_reset(db: DbSession, *, user: User) -> None:
    """Mark the user's issued reset request(s) completed after a forced change and
    invalidate any lingering unconsumed grants so no temporary password survives."""
    db.execute(
        update(TemporaryPasswordGrant)
        .where(
            TemporaryPasswordGrant.user_id == user.id,
            TemporaryPasswordGrant.consumed_at.is_(None),
        )
        .values(consumed_at=_utcnow())
    )
    reqs = db.scalars(
        select(PasswordResetRequest).where(
            PasswordResetRequest.user_id == user.id,
            PasswordResetRequest.status == ResetStatus.issued,
        )
    ).all()
    for r in reqs:
        r.status = ResetStatus.completed
        r.completed_at = _utcnow()
