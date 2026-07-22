"""Idempotent bootstrap-Administrator setup command.

Creates the first Administrator transactionally ONLY when no users exist. The
password is prompted interactively or generated and shown exactly once; it is
never written to logs. Re-running when any user exists makes no changes.

Usage:
    python -m src.core.setup
"""

from __future__ import annotations

import getpass
import os
import secrets
import sys

from sqlalchemy import func, select

from ..models.base import Role, UserStatus
from ..models.user import User
from ..services import audit
from .db import SessionLocal
from .password_policy import PasswordPolicyError, validate_password
from .schema import create_all
from .security import hash_password
from .username import UsernameError, validate_username

_DEFAULT_FORBIDDEN = {"admin", "administrator", "root", "password"}


def _read_password() -> tuple[str, bool]:
    """Return (password, generated?).

    Resolution order:
    1. ``LIBRARY_BOOTSTRAP_PASSWORD`` env var (for automated provisioning/CI).
    2. Interactive prompt when a TTY is available.
    3. Otherwise generate a strong password and show it once.
    """
    env_pw = os.environ.get("LIBRARY_BOOTSTRAP_PASSWORD")
    if env_pw:
        return env_pw, False
    if sys.stdin and sys.stdin.isatty():
        pw = getpass.getpass("Set bootstrap administrator password: ")
        confirm = getpass.getpass("Confirm password: ")
        if pw != confirm:
            raise SystemExit("Passwords do not match.")
        return pw, False
    # Non-interactive: generate a strong password and show it once.
    return secrets.token_urlsafe(16) + "1a", True


def run(username: str = "admin") -> None:
    create_all()
    db = SessionLocal()
    try:
        existing = db.scalar(select(func.count()).select_from(User))
        if existing and existing > 0:
            print("Users already exist; setup is a no-op.")
            return

        try:
            display, normalized = validate_username(username)
        except UsernameError as exc:
            raise SystemExit(f"Invalid administrator username: {exc}")
        if normalized in _DEFAULT_FORBIDDEN and display.casefold() == normalized:
            # Allow the literal default username but never a default password.
            pass

        password, generated = _read_password()
        if password.casefold() in _DEFAULT_FORBIDDEN:
            raise SystemExit("Refusing to use a default/well-known password.")
        try:
            validate_password(password)
        except PasswordPolicyError as exc:
            raise SystemExit(f"Password does not meet policy: {exc}")

        admin = User(
            username=display,
            username_normalized=normalized,
            password_hash=hash_password(password),
            role=Role.administrator,
            status=UserStatus.active,
            force_password_change=True,
        )
        db.add(admin)
        db.flush()
        audit.record(
            db,
            action="user.bootstrap_admin",
            target_id=admin.id,
            reason="initial administrator provisioning",
        )
        db.commit()

        print(f"Bootstrap administrator '{display}' created. You must change the password on first login.")
        if generated:
            print("Generated one-time password (shown once, store securely):")
            print(f"    {password}")
    finally:
        db.close()


if __name__ == "__main__":  # pragma: no cover
    run()
