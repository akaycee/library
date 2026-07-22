"""Schemas for the password-reset flow."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ResetRequestBody(BaseModel):
    username: str = Field(max_length=64)


class ResetReceived(BaseModel):
    status: str = "received"


class TemporaryLoginBody(BaseModel):
    username: str = Field(max_length=64)
    temporary_password: str = Field(max_length=256)


class ChangePasswordBody(BaseModel):
    # Required for a normal (full-session) change; ignored for a forced change
    # made from a restricted password-change session.
    current_password: str | None = Field(default=None, max_length=256)
    new_password: str = Field(max_length=256)


class PendingResetView(BaseModel):
    id: str
    username: str
    status: str
    requested_at: datetime


class IssuedTemporaryPassword(BaseModel):
    temporary_password: str
    expires_at: datetime
