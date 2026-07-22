"""Location model — an adjacency-list tree node."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Location(Base):
    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_locations_parent_name", "parent_id", "name_normalized"),
        # No two live siblings may share a normalized name (best-effort DB guard;
        # NULL parents are treated as distinct by SQLite so the app also checks).
        Index(
            "uq_locations_parent_name_live",
            "parent_id",
            "name_normalized",
            unique=True,
            sqlite_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(100), nullable=False)
    type_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    parent_id: Mapped[str | None] = mapped_column(
        ForeignKey("locations.id"), nullable=True, index=True
    )
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    # Soft deletion (constitution: retain history; never physically delete).
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
