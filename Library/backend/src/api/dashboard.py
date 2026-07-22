"""Dashboard router (F9): a single staff-only read endpoint that returns the
at-a-glance summary, overdue loans, and recent circulation activity."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..services import dashboard as svc
from .deps import require_staff
from .loans import LoanView, _view

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class ActivityView(BaseModel):
    action: str
    reason: str | None
    created_at: datetime


class SummaryView(BaseModel):
    titles: int
    copies: int
    on_loan: int
    available: int
    overdue: int
    active_borrowers: int
    pending_resets: int
    overdue_loans: list[LoanView]
    recent_activity: list[ActivityView]


@router.get("/summary", response_model=SummaryView)
def get_summary(_staff=Depends(require_staff), db: DbSession = Depends(get_db)) -> SummaryView:
    s = svc.summary(db)
    return SummaryView(
        titles=s.titles,
        copies=s.copies,
        on_loan=s.on_loan,
        available=s.available,
        overdue=s.overdue,
        active_borrowers=s.active_borrowers,
        pending_resets=s.pending_resets,
        overdue_loans=[_view(r) for r in s.overdue_loans],
        recent_activity=[
            ActivityView(action=a.action, reason=a.reason, created_at=a.created_at)
            for a in s.recent_activity
        ],
    )
