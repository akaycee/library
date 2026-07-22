"""Loan model — a borrowing record tying a Copy to a borrower."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Loan(Base):
    __tablename__ = "loans"
    __table_args__ = (
        # A copy may have at most one active (not-yet-returned) loan. Enforced at
        # the database level so concurrent checkouts cannot double-loan a copy.
        Index(
            "uq_active_loan_per_copy",
            "copy_id",
            unique=True,
            sqlite_where=text("returned_at IS NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    copy_id: Mapped[str] = mapped_column(ForeignKey("copies.id"), nullable=False, index=True)
    borrower_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    checked_out_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    borrowed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    renewal_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
