"""Dashboard service (F9): derives an at-a-glance staff snapshot on demand.

All figures come from live data (copies, loans, reset requests, audit log); no
denormalized counters are introduced. Overdue rows reuse the circulation service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession

from ..models.audit import AuditLogEntry
from ..models.base import CopyStatus, ResetStatus
from ..models.copy import Copy
from ..models.loan import Loan
from ..models.reset import PasswordResetRequest
from ..models.title import Title
from . import circulation


@dataclass
class ActivityRow:
    action: str
    reason: str | None
    created_at: datetime


@dataclass
class DashboardSummary:
    titles: int
    copies: int
    on_loan: int
    available: int
    overdue: int
    active_borrowers: int
    pending_resets: int
    overdue_loans: list[circulation.LoanRow]
    recent_activity: list[ActivityRow]


def recent_activity(db: DbSession, *, limit: int = 10) -> list[ActivityRow]:
    rows = db.scalars(
        select(AuditLogEntry)
        .where(AuditLogEntry.action.like("loan.%"))
        .order_by(AuditLogEntry.created_at.desc())
        .limit(limit)
    ).all()
    return [
        ActivityRow(action=r.action, reason=r.reason, created_at=r.created_at)
        for r in rows
    ]


def summary(db: DbSession) -> DashboardSummary:
    titles = db.scalar(
        select(func.count()).select_from(Title).where(Title.deleted_at.is_(None))
    ) or 0
    copies = db.scalar(
        select(func.count()).select_from(Copy).where(Copy.deleted_at.is_(None))
    ) or 0
    on_loan = (
        db.scalar(
            select(func.count())
            .select_from(Copy)
            .where(Copy.status == CopyStatus.checked_out, Copy.deleted_at.is_(None))
        )
        or 0
    )
    available = (
        db.scalar(
            select(func.count())
            .select_from(Copy)
            .where(Copy.status == CopyStatus.available, Copy.deleted_at.is_(None))
        )
        or 0
    )
    active_borrowers = (
        db.scalar(
            select(func.count(func.distinct(Loan.borrower_id))).where(Loan.returned_at.is_(None))
        )
        or 0
    )
    pending_resets = (
        db.scalar(
            select(func.count())
            .select_from(PasswordResetRequest)
            .where(PasswordResetRequest.status == ResetStatus.pending)
        )
        or 0
    )

    overdue_loans = circulation.list_active(db, overdue_only=True)

    return DashboardSummary(
        titles=titles,
        copies=copies,
        on_loan=on_loan,
        available=available,
        overdue=len(overdue_loans),
        active_borrowers=active_borrowers,
        pending_resets=pending_resets,
        overdue_loans=overdue_loans,
        recent_activity=recent_activity(db),
    )
