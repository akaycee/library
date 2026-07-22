"""Circulation service: checkout, return, renew, and loan lists.

Staff-only desk model. Checkout sets the copy `checked_out` and creates a Loan;
return restores `available`. Overdue is derived (due_at < now, not returned).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession

from ..models.base import CopyStatus, Role, UserStatus
from ..models.copy import Copy
from ..models.loan import Loan
from ..models.title import Title
from ..models.user import User
from . import audit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


class CirculationError(Exception):
    pass


class CopyNotFoundError(CirculationError):
    pass


class BorrowerNotFoundError(CirculationError):
    pass


class CopyNotAvailableError(CirculationError):
    pass


class InvalidLoanPeriodError(CirculationError):
    pass


class LoanNotFoundError(CirculationError):
    pass


class LoanNotActiveError(CirculationError):
    pass


class OverdueRenewalError(CirculationError):
    pass


@dataclass
class LoanRow:
    id: str
    copy_id: str
    barcode: str
    title_name: str
    borrower_username: str
    borrowed_at: datetime
    due_at: datetime
    renewal_count: int
    overdue: bool


def _row(db: DbSession, loan: Loan) -> LoanRow:
    copy = db.get(Copy, loan.copy_id)
    title = db.get(Title, copy.title_id) if copy else None
    borrower = db.get(User, loan.borrower_id)
    return LoanRow(
        id=loan.id,
        copy_id=loan.copy_id,
        barcode=copy.barcode if copy else "?",
        title_name=title.name if title else "?",
        borrower_username=borrower.username if borrower else "?",
        borrowed_at=loan.borrowed_at,
        due_at=loan.due_at,
        renewal_count=loan.renewal_count,
        overdue=loan.returned_at is None and _utcnow() > _aware(loan.due_at),
    )


def checkout(
    db: DbSession, *, actor_id: str, barcode: str, borrower_username: str, loan_period_days: int
) -> Loan:
    if loan_period_days is None or loan_period_days <= 0:
        raise InvalidLoanPeriodError("loan period must be a positive number of days")

    copy = db.scalar(select(Copy).where(Copy.barcode == barcode.strip()))
    if copy is None:
        raise CopyNotFoundError("no copy with that barcode")
    if copy.status != CopyStatus.available:
        raise CopyNotAvailableError("that copy is not available")

    normalized = (borrower_username or "").strip().casefold()
    borrower = db.scalar(select(User).where(User.username_normalized == normalized))
    if borrower is None or borrower.status != UserStatus.active or borrower.role != Role.borrower:
        raise BorrowerNotFoundError("no active borrower with that username")

    now = _utcnow()
    loan = Loan(
        copy_id=copy.id,
        borrower_id=borrower.id,
        checked_out_by=actor_id,
        borrowed_at=now,
        due_at=now + timedelta(days=loan_period_days),
    )
    copy.status = CopyStatus.checked_out
    db.add(loan)
    try:
        # Flush now so the "one active loan per copy" unique index fires here and
        # a concurrent second checkout of the same copy is rejected atomically.
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise CopyNotAvailableError("that copy is not available") from exc
    audit.record(
        db, action="loan.checkout", actor_id=actor_id, target_id=borrower.id,
        reason=f"checked out {copy.barcode} to {borrower.username} for {loan_period_days}d", detail=loan.id,
    )
    return loan


def _get_loan(db: DbSession, loan_id: str) -> Loan:
    loan = db.get(Loan, loan_id)
    if loan is None:
        raise LoanNotFoundError("loan not found")
    return loan


def return_loan(db: DbSession, *, actor_id: str, loan_id: str) -> Loan:
    loan = _get_loan(db, loan_id)
    if loan.returned_at is not None:
        raise LoanNotActiveError("that loan is already returned")
    loan.returned_at = _utcnow()
    copy = db.get(Copy, loan.copy_id)
    if copy is not None and copy.status == CopyStatus.checked_out:
        copy.status = CopyStatus.available
    db.flush()
    audit.record(
        db, action="loan.return", actor_id=actor_id, target_id=loan.borrower_id,
        reason=f"returned loan {loan.id}", detail=loan.id,
    )
    return loan


def renew(db: DbSession, *, actor_id: str, loan_id: str, days: int) -> Loan:
    if days is None or days <= 0:
        raise InvalidLoanPeriodError("renewal days must be positive")
    loan = _get_loan(db, loan_id)
    if loan.returned_at is not None:
        raise LoanNotActiveError("that loan is already returned")
    if _utcnow() > _aware(loan.due_at):
        raise OverdueRenewalError("cannot renew an overdue loan")
    loan.due_at = _aware(loan.due_at) + timedelta(days=days)
    loan.renewal_count += 1
    db.flush()
    audit.record(
        db, action="loan.renew", actor_id=actor_id, target_id=loan.borrower_id,
        reason=f"renewed loan {loan.id} by {days}d", detail=loan.id,
    )
    return loan


def list_active(db: DbSession, *, overdue_only: bool = False) -> list[LoanRow]:
    loans = db.scalars(
        select(Loan).where(Loan.returned_at.is_(None)).order_by(Loan.due_at)
    ).all()
    rows = [_row(db, l) for l in loans]
    if overdue_only:
        rows = [r for r in rows if r.overdue]
    return rows


def list_for_borrower(db: DbSession, *, borrower_id: str) -> list[LoanRow]:
    loans = db.scalars(
        select(Loan)
        .where(Loan.borrower_id == borrower_id, Loan.returned_at.is_(None))
        .order_by(Loan.due_at)
    ).all()
    return [_row(db, l) for l in loans]
