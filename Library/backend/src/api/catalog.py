"""Catalog router (staff only): titles and copies."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..schemas.catalog import (
    CopyCreate,
    CopyStatusUpdate,
    CopyUpdate,
    CopyView,
    TitleCreate,
    TitleDetail,
    TitleUpdate,
    TitleView,
)
from ..services import catalog as svc
from .deps import require_staff, require_staff_write

router = APIRouter(tags=["catalog"])


def _copy_view(db: DbSession, c) -> CopyView:
    row = svc.copy_row(db, c)
    return CopyView(
        id=row.id,
        barcode=row.barcode,
        location_id=row.location_id,
        location_path=row.location_path,
        status=row.status,
        condition=row.condition,
    )


# --- Titles -------------------------------------------------------------------
@router.get("/titles", response_model=list[TitleView])
def list_titles(_staff=Depends(require_staff), db: DbSession = Depends(get_db)) -> list[TitleView]:
    return [
        TitleView(
            id=t.id, name=t.name, author=t.author, isbn=t.isbn, media_type=t.media_type,
            copy_count=count,
        )
        for t, count in svc.list_titles(db)
    ]


@router.post("/titles", status_code=status.HTTP_201_CREATED, response_model=TitleView)
def create_title(payload: TitleCreate, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> TitleView:
    try:
        t = svc.create_title(
            db, actor_id=staff.user.id, name=payload.name, author=payload.author,
            isbn=payload.isbn, media_type=payload.media_type,
        )
    except svc.CatalogError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return TitleView(id=t.id, name=t.name, author=t.author, isbn=t.isbn, media_type=t.media_type, copy_count=0)


@router.get("/titles/{title_id}", response_model=TitleDetail)
def get_title(title_id: str, _staff=Depends(require_staff), db: DbSession = Depends(get_db)) -> TitleDetail:
    try:
        title, copies = svc.get_title(db, title_id)
    except svc.TitleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="title not found") from exc
    return TitleDetail(
        id=title.id, name=title.name, author=title.author, isbn=title.isbn,
        media_type=title.media_type, copies=[_copy_view(db, c) for c in copies],
    )


@router.patch("/titles/{title_id}", response_model=TitleView)
def update_title(title_id: str, payload: TitleUpdate, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> TitleView:
    try:
        t = svc.update_title(
            db, actor_id=staff.user.id, title_id=title_id, name=payload.name, author=payload.author,
            isbn=payload.isbn, media_type=payload.media_type, fields_set=payload.model_fields_set,
        )
    except svc.TitleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="title not found") from exc
    except svc.CatalogError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    _t, count = next(((x, c) for x, c in svc.list_titles(db) if x.id == t.id), (t, 0))
    return TitleView(id=t.id, name=t.name, author=t.author, isbn=t.isbn, media_type=t.media_type, copy_count=count)


@router.delete("/titles/{title_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_title(title_id: str, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> Response:
    try:
        svc.delete_title(db, actor_id=staff.user.id, title_id=title_id)
    except svc.TitleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="title not found") from exc
    except svc.TitleHasCopiesError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Copies -------------------------------------------------------------------
@router.post("/titles/{title_id}/copies", status_code=status.HTTP_201_CREATED, response_model=CopyView)
def add_copy(title_id: str, payload: CopyCreate, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> CopyView:
    try:
        c = svc.add_copy(
            db, actor_id=staff.user.id, title_id=title_id, location_id=payload.location_id,
            barcode=payload.barcode, condition=payload.condition,
        )
    except (svc.TitleNotFoundError, svc.LocationNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except svc.DuplicateBarcodeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return _copy_view(db, c)


@router.patch("/copies/{copy_id}", response_model=CopyView)
def update_copy(copy_id: str, payload: CopyUpdate, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> CopyView:
    try:
        c = svc.move_copy(
            db, actor_id=staff.user.id, copy_id=copy_id, location_id=payload.location_id,
            condition=payload.condition, fields_set=payload.model_fields_set,
        )
    except svc.CopyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="copy not found") from exc
    except svc.LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.commit()
    return _copy_view(db, c)


@router.patch("/copies/{copy_id}/status", response_model=CopyView)
def set_copy_status(copy_id: str, payload: CopyStatusUpdate, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> CopyView:
    try:
        c = svc.set_copy_status(db, actor_id=staff.user.id, copy_id=copy_id, new_status=payload.status)
    except svc.CopyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="copy not found") from exc
    except svc.InvalidStatusError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except svc.CopyCheckedOutError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return _copy_view(db, c)


@router.delete("/copies/{copy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_copy(copy_id: str, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)) -> Response:
    try:
        svc.delete_copy(db, actor_id=staff.user.id, copy_id=copy_id)
    except svc.CopyNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="copy not found") from exc
    except svc.CopyCheckedOutError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
