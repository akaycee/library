"""Browse & search router — read-only, any authenticated role."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..services import browse as svc
from .deps import get_current

router = APIRouter(prefix="/browse", tags=["browse"])


class BrowseItem(BaseModel):
    id: str
    name: str
    author: str | None = None
    media_type: str | None = None
    available_count: int
    total_count: int


@router.get("", response_model=list[BrowseItem])
def browse(
    q: str | None = None, _user=Depends(get_current), db: DbSession = Depends(get_db)
) -> list[BrowseItem]:
    return [
        BrowseItem(
            id=r.id, name=r.name, author=r.author, media_type=r.media_type,
            available_count=r.available_count, total_count=r.total_count,
        )
        for r in svc.search_titles(db, q)
    ]
