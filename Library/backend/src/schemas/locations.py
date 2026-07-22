"""Schemas for location management."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LocationNode(BaseModel):
    id: str
    name: str
    type_label: str | None = None
    parent_id: str | None = None
    children: list["LocationNode"] = Field(default_factory=list)


LocationNode.model_rebuild()


class LocationView(BaseModel):
    id: str
    name: str
    type_label: str | None = None
    parent_id: str | None = None


class CreateLocation(BaseModel):
    name: str = Field(max_length=100)
    type_label: str | None = Field(default=None, max_length=50)
    parent_id: str | None = None


class UpdateLocation(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    type_label: str | None = Field(default=None, max_length=50)


class MoveLocation(BaseModel):
    new_parent_id: str | None = None
