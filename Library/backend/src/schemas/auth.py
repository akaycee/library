"""Pydantic request/response schemas for authentication."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..models.base import Role


class RegisterRequest(BaseModel):
    # Bounds guard against oversized payloads; friendly field-level validation is
    # performed by the service layer (username/password validators).
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)


class LoginRequest(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)


class UserPublic(BaseModel):
    id: str
    username: str
    role: Role


class MeResponse(BaseModel):
    id: str
    username: str
    role: Role
    force_password_change: bool
