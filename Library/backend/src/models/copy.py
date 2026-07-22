"""Copy model — a physical item belonging to a Title, living at a Location."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, CopyStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Copy(Base):
    __tablename__ = "copies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title_id: Mapped[str] = mapped_column(ForeignKey("titles.id"), nullable=False, index=True)
    barcode: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.id"), nullable=False, index=True)
    status: Mapped[CopyStatus] = mapped_column(
        Enum(CopyStatus), nullable=False, default=CopyStatus.available
    )
    condition: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )
    # Soft deletion (constitution: retain history; never physically delete).
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
