"""Pydantic schemas for administrator user management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..models.base import Role, UserStatus


class CreateUserRequest(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=256)
    role: Role


class RoleUpdate(BaseModel):
    role: Role


class StatusUpdate(BaseModel):
    status: UserStatus


class UserAdminView(BaseModel):
    id: str
    username: str
    role: Role
    status: UserStatus
    force_password_change: bool
    created_at: datetime
