"""SQLAlchemy declarative base and shared enums."""

from __future__ import annotations

import enum

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Role(str, enum.Enum):
    administrator = "administrator"
    librarian = "librarian"
    borrower = "borrower"


class UserStatus(str, enum.Enum):
    active = "active"
    deactivated = "deactivated"


class SessionKind(str, enum.Enum):
    full = "full"
    password_change = "password_change"


class ResetStatus(str, enum.Enum):
    pending = "pending"
    issued = "issued"
    completed = "completed"
    expired = "expired"
    cancelled = "cancelled"


class CopyStatus(str, enum.Enum):
    available = "available"
    checked_out = "checked_out"
    lost = "lost"
    withdrawn = "withdrawn"
