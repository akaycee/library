"""Security primitives: password hashing, opaque tokens, and CSRF helpers."""

from __future__ import annotations

import hashlib
import hmac
import secrets

from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password with Argon2id."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        return False


def generate_token(num_bytes: int = 32) -> str:
    """Generate an opaque, URL-safe random token."""
    return secrets.token_urlsafe(num_bytes)


def hash_token(token: str) -> str:
    """Hash an opaque token (session/temp) for storage. SHA-256 is sufficient for
    high-entropy random tokens (unlike low-entropy passwords)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)
