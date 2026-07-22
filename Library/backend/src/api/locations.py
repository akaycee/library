"""Location management router (staff only: Administrator or Librarian)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session as DbSession

from ..core.db import get_db
from ..core.locations_name import LocationNameError
from ..schemas.locations import (
    CreateLocation,
    LocationNode,
    LocationView,
    MoveLocation,
    UpdateLocation,
)
from ..services import locations as loc_service
from .deps import require_staff, require_staff_write

router = APIRouter(prefix="/locations", tags=["locations"])


def _to_node(n: loc_service.TreeNode) -> LocationNode:
    return LocationNode(
        id=n.id,
        name=n.name,
        type_label=n.type_label,
        parent_id=n.parent_id,
        children=[_to_node(c) for c in n.children],
    )


def _view(loc) -> LocationView:
    return LocationView(id=loc.id, name=loc.name, type_label=loc.type_label, parent_id=loc.parent_id)


@router.get("", response_model=list[LocationNode])
def list_locations(_staff=Depends(require_staff), db: DbSession = Depends(get_db)) -> list[LocationNode]:
    return [_to_node(n) for n in loc_service.list_tree(db)]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LocationView)
def create_location(
    payload: CreateLocation, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)
) -> LocationView:
    try:
        loc = loc_service.create(
            db,
            actor_id=staff.user.id,
            name=payload.name,
            type_label=payload.type_label,
            parent_id=payload.parent_id,
        )
    except loc_service.LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="parent not found") from exc
    except loc_service.DuplicateSiblingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except loc_service.MaxDepthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LocationNameError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return _view(loc)


@router.patch("/{location_id}", response_model=LocationView)
def update_location(
    location_id: str,
    payload: UpdateLocation,
    staff=Depends(require_staff_write),
    db: DbSession = Depends(get_db),
) -> LocationView:
    try:
        loc = loc_service.rename(
            db,
            actor_id=staff.user.id,
            location_id=location_id,
            name=payload.name,
            type_label=payload.type_label,
            type_label_provided="type_label" in payload.model_fields_set,
        )
    except loc_service.LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="location not found") from exc
    except loc_service.DuplicateSiblingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except LocationNameError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return _view(loc)


@router.patch("/{location_id}/move", response_model=LocationView)
def move_location(
    location_id: str,
    payload: MoveLocation,
    staff=Depends(require_staff_write),
    db: DbSession = Depends(get_db),
) -> LocationView:
    try:
        loc = loc_service.move(
            db, actor_id=staff.user.id, location_id=location_id, new_parent_id=payload.new_parent_id
        )
    except loc_service.LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="location not found") from exc
    except loc_service.CycleError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except loc_service.DuplicateSiblingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except loc_service.MaxDepthError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return _view(loc)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: str, staff=Depends(require_staff_write), db: DbSession = Depends(get_db)
) -> Response:
    try:
        loc_service.delete(db, actor_id=staff.user.id, location_id=location_id)
    except loc_service.LocationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="location not found") from exc
    except loc_service.NotEmptyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
