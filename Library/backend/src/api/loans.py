"""Loans / circulation router. Mutations + active lists are staff-only;
`/loans/mine` is available to any authenticated user (their own loans)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..services import circulation as svc
from .deps import get_current, require_staff, require_staff_write

router = APIRouter(prefix="/loans", tags=["loans"])


class CheckoutBody(BaseModel):
    barcode: str
    borrower_username: str
    loan_period_days: int = Field(gt=0)


class RenewBody(BaseModel):
    days: int = Field(gt=0)


class LoanView(BaseModel):
    id: str
    copy_id: str
    barcode: str
    title_name: str
    borrower_username: str
    borrowed_at: datetime
    due_at: datetime
    renewal_count: int
    overdue: bool


def _view(r: svc.LoanRow) -> LoanView:
    return LoanView(
        id=r.id, copy_id=r.copy_id, barcode=r.barcode, title_name=r.title_name,
        borrower_username=r.borrower_username, borrowed_at=r.borrowed_at, due_at=r.due_at,
        renewal_count=r.renewal_count, overdue=r.overdue,
    )


@router.get("", response_model=list[LoanView])
def list_loans(status_filter: str | None = None, _staff=Depends(require_staff), db: DbSession = Depends(get_db)) -> list[LoanView]:
    overdue_only = (status_filter or "").lower() == "overdue"
    return [_view(r) for r in svc.list_active(db, overdue_only=overdue_only)]


@router.get("/mine", response_model=list[LoanView])
def my_loans(current=Depends(get_current), db: DbSession = Depends(get_db)) -> list[LoanView]:
    return [_view(r) for r in svc.list_for_borrower(db, borrower_id=current.user.id)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LoanView)
def checkout(payload: CheckoutBody, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> LoanView:
    try:
        loan = svc.checkout(
            db, actor_id=staff.user.id, barcode=payload.barcode,
            borrower_username=payload.borrower_username, loan_period_days=payload.loan_period_days,
        )
    except (svc.CopyNotFoundError, svc.BorrowerNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except svc.CopyNotAvailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except svc.InvalidLoanPeriodError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return _view(svc._row(db, loan))


@router.post("/{loan_id}/return", response_model=LoanView)
def return_loan(loan_id: str, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> LoanView:
    try:
        loan = svc.return_loan(db, actor_id=staff.user.id, loan_id=loan_id)
    except svc.LoanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="loan not found") from exc
    except svc.LoanNotActiveError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return _view(svc._row(db, loan))


@router.post("/{loan_id}/renew", response_model=LoanView)
def renew(loan_id: str, payload: RenewBody, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> LoanView:
    try:
        loan = svc.renew(db, actor_id=staff.user.id, loan_id=loan_id, days=payload.days)
    except svc.LoanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="loan not found") from exc
    except svc.LoanNotActiveError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except svc.OverdueRenewalError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except svc.InvalidLoanPeriodError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return _view(svc._row(db, loan))
