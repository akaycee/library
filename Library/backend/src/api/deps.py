"""Shared API dependencies: current user resolution and CSRF enforcement."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session as DbSession

from ..core.config import get_settings
from ..core.db import get_db
from ..core.security import constant_time_equals
from ..models.base import Role, SessionKind
from ..services import sessions as session_service


def get_session_any(request: Request, db: DbSession = Depends(get_db)):
    """Resolve any valid session (full or restricted password-change)."""
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    resolved = session_service.resolve_session(db, token)
    # Persist the refreshed last_seen_at (idle-timeout sliding window) and any
    # idle revocation so continuous browsing actually keeps the session alive.
    db.commit()
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    return resolved


def get_current(resolved=Depends(get_session_any)):
    """Full-access session. Restricted password-change sessions are rejected so
    they can only reach the change-password endpoint."""
    if resolved.session.kind == SessionKind.password_change:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    return resolved


def _check_csrf(resolved, x_csrf_token: str | None) -> None:
    if not x_csrf_token or not constant_time_equals(x_csrf_token, resolved.session.csrf_token):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid CSRF token")


def _origin_host(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value)
    return parsed.netloc or None


def enforce_trusted_origin(request: Request) -> None:
    """Reject state-changing requests whose ``Origin``/``Referer`` does not match
    the target host. Browsers always attach ``Origin`` to cross-site POSTs, so
    this blocks CSRF even before the token check. Non-browser clients and same-
    origin requests (no/aligned Origin) are allowed."""
    host = request.headers.get("host")
    origin_host = _origin_host(request.headers.get("origin"))
    if origin_host is not None:
        if origin_host != host:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="cross-origin request rejected"
            )
        return
    referer_host = _origin_host(request.headers.get("referer"))
    if referer_host is not None and referer_host != host:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="cross-origin request rejected"
        )


def require_csrf(
    request: Request,
    x_csrf_token: str | None = Header(default=None),
    current=Depends(get_current),
):
    """Double-submit CSRF check + trusted-origin validation for authenticated
    (full-session) state changes."""
    enforce_trusted_origin(request)
    _check_csrf(current, x_csrf_token)
    return current


def require_csrf_any(
    request: Request,
    x_csrf_token: str | None = Header(default=None),
    resolved=Depends(get_session_any),
):
    """CSRF + origin check that also accepts a restricted password-change session
    (used by the change-password endpoint)."""
    enforce_trusted_origin(request)
    _check_csrf(resolved, x_csrf_token)
    return resolved


def require_admin(current=Depends(get_current)):
    """Read-side guard: caller must be an active Administrator."""
    if current.user.role != Role.administrator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to do that."
        )
    return current


def require_admin_write(current=Depends(require_csrf)):
    """Write-side guard: Administrator role + valid CSRF token."""
    if current.user.role != Role.administrator:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to do that."
        )
    return current


_STAFF_ROLES = (Role.administrator, Role.librarian)


def require_staff(current=Depends(get_current)):
    """Read-side guard: caller must be staff (Administrator or Librarian)."""
    if current.user.role not in _STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to do that."
        )
    return current


def require_staff_write(current=Depends(require_csrf)):
    """Write-side guard: staff role + valid CSRF token."""
    if current.user.role not in _STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to do that."
        )
    return current
