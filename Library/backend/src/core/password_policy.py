"""Password policy validation, enforced consistently at registration,
admin user-creation, and password change/reset (FR-004)."""

from __future__ import annotations

from .config import get_settings


class PasswordPolicyError(ValueError):
    """Raised when a password fails the policy."""


def validate_password(password: str) -> None:
    """Validate against the configured policy. Raises PasswordPolicyError."""
    settings = get_settings()
    if password is None or len(password) < settings.password_min_length:
        raise PasswordPolicyError(
            f"password must be at least {settings.password_min_length} characters"
        )
    if not any(c.isalpha() for c in password):
        raise PasswordPolicyError("password must contain at least one letter")
    if not any(c.isdigit() for c in password):
        raise PasswordPolicyError("password must contain at least one number")
