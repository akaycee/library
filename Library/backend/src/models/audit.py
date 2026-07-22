"""Append-only audit log. Records who / what / when / why (constitution II)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )  # null for system/bootstrap
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    target_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    # Polymorphic pointer to a non-user entity affected by the action (e.g. a
    # title/copy/location). No FK: it may reference different tables and must
    # survive soft-deletion of the referent.
    entity_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)  # the "why"
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)  # before/after (JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
