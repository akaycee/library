"""Schemas for the catalog (titles and copies)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..models.base import CopyStatus


class TitleCreate(BaseModel):
    name: str = Field(max_length=255)
    author: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=32)
    media_type: str | None = Field(default=None, max_length=50)


class TitleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    isbn: str | None = Field(default=None, max_length=32)
    media_type: str | None = Field(default=None, max_length=50)


class TitleView(BaseModel):
    id: str
    name: str
    author: str | None = None
    isbn: str | None = None
    media_type: str | None = None
    copy_count: int


class CopyView(BaseModel):
    id: str
    barcode: str
    location_id: str
    location_path: str
    status: CopyStatus
    condition: str | None = None


class TitleDetail(BaseModel):
    id: str
    name: str
    author: str | None = None
    isbn: str | None = None
    media_type: str | None = None
    copies: list[CopyView]


class CopyCreate(BaseModel):
    location_id: str
    barcode: str | None = Field(default=None, max_length=64)
    condition: str | None = Field(default=None, max_length=120)


class CopyUpdate(BaseModel):
    location_id: str | None = None
    condition: str | None = Field(default=None, max_length=120)


class CopyStatusUpdate(BaseModel):
    status: CopyStatus
