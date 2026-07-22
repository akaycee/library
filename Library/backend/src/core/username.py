"""Username normalization and validation.

Uniqueness is enforced on the normalized form so it is portable across
SQLite/SQLCipher and PostgreSQL without relying on database collation.
"""

from __future__ import annotations

import re
import unicodedata

from .config import get_settings

_ALLOWED_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class UsernameError(ValueError):
    """Raised when a username fails validation."""


def normalize_username(raw: str) -> str:
    """Trim, NFKC-normalize, and case-fold a username into its canonical form."""
    if raw is None:
        raise UsernameError("username required")
    trimmed = raw.strip()
    if not trimmed:
        raise UsernameError("username must not be empty")
    normalized = unicodedata.normalize("NFKC", trimmed).casefold()
    return normalized


def validate_username(raw: str) -> tuple[str, str]:
    """Validate a username and return (display, normalized).

    - display: the trimmed, NFKC-normalized form as entered (preserving case)
    - normalized: the case-folded canonical form used for uniqueness/lookup
    """
    settings = get_settings()
    if raw is None:
        raise UsernameError("username required")
    display = unicodedata.normalize("NFKC", raw.strip())
    if not display:
        raise UsernameError("username must not be empty")
    if len(display) > settings.username_max_length:
        raise UsernameError(f"username must be at most {settings.username_max_length} characters")
    if not _ALLOWED_RE.match(display):
        raise UsernameError("username may only contain letters, digits, and . _ -")
    return display, display.casefold()
