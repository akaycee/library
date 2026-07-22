"""Authentication router: register, login, logout, me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session as DbSession

from ..core.config import get_settings
from ..core.db import get_db
from ..core.password_policy import PasswordPolicyError
from ..core.username import UsernameError
from ..models.base import SessionKind
from ..schemas.auth import LoginRequest, MeResponse, RegisterRequest, UserPublic
from ..schemas.reset import (
    ChangePasswordBody,
    ResetReceived,
    ResetRequestBody,
    TemporaryLoginBody,
)
from ..services import auth as auth_service
from ..services import reset as reset_service
from ..services import sessions as session_service
from .deps import enforce_trusted_origin, get_current, require_csrf, require_csrf_any

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _set_session_cookies(response: Response, issued: session_service.IssuedSession) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=issued.session_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_absolute_ttl_seconds,
    )
    # CSRF cookie is readable by JS (double-submit) and echoed via X-CSRF-Token.
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=issued.csrf_token,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="strict",
        max_age=settings.session_absolute_ttl_seconds,
    )


def _clear_session_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name)
    response.delete_cookie(settings.csrf_cookie_name)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserPublic)
def register(
    payload: RegisterRequest,
    db: DbSession = Depends(get_db),
    _origin=Depends(enforce_trusted_origin),
) -> UserPublic:
    try:
        user = auth_service.register_borrower(
            db, username=payload.username, password=payload.password
        )
    except auth_service.UsernameTakenError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="username unavailable") from exc
    except (UsernameError, PasswordPolicyError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    return UserPublic(id=user.id, username=user.username, role=user.role)


@router.post("/login", response_model=MeResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession = Depends(get_db),
    _origin=Depends(enforce_trusted_origin),
) -> MeResponse:
    try:
        user = auth_service.authenticate(
            db, username=payload.username, password=payload.password, client=_client_id(request)
        )
    except auth_service.InvalidCredentialsError as exc:
        # Indistinguishable, user-facing response for invalid / unknown / locked.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
        ) from exc
    # Session rotation: revoke whatever session token this client already presents
    # so a fresh login never leaves a second, still-valid session behind.
    settings = get_settings()
    presented = request.cookies.get(settings.session_cookie_name)
    if presented:
        session_service.revoke_session_by_token(db, presented)
    # Accounts flagged for a mandatory password change get a RESTRICTED session
    # that backend guards reject everywhere except change-password — the redirect
    # is not the only gate.
    kind = (
        SessionKind.password_change if user.force_password_change else SessionKind.full
    )
    issued = session_service.create_session(db, user, kind=kind)
    db.commit()
    _set_session_cookies(response, issued)
    return MeResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        force_password_change=user.force_password_change,
    )


@router.post("/logout")
def logout(
    request: Request, response: Response, db: DbSession = Depends(get_db), _=Depends(require_csrf)
) -> dict[str, str]:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    session_service.revoke_session_by_token(db, token)
    db.commit()
    _clear_session_cookies(response)
    return {"status": "logged_out"}


@router.get("/me", response_model=MeResponse)
def me(current=Depends(get_current)) -> MeResponse:
    user = current.user
    return MeResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        force_password_change=user.force_password_change,
    )


@router.post("/reset-requests", status_code=status.HTTP_202_ACCEPTED, response_model=ResetReceived)
def request_reset(
    payload: ResetRequestBody,
    request: Request,
    db: DbSession = Depends(get_db),
    _origin=Depends(enforce_trusted_origin),
) -> ResetReceived:
    # Identical response whether or not the username exists (no enumeration).
    try:
        reset_service.submit_request(db, username=payload.username, client=_client_id(request))
    except reset_service.RateLimitedError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a moment and try again.",
        ) from exc
    db.commit()
    return ResetReceived()


@router.post("/login-temporary", response_model=MeResponse)
def login_temporary(
    payload: TemporaryLoginBody,
    response: Response,
    db: DbSession = Depends(get_db),
    _origin=Depends(enforce_trusted_origin),
) -> MeResponse:
    try:
        user = reset_service.consume_temporary_login(
            db, username=payload.username, temporary_password=payload.temporary_password
        )
    except reset_service.InvalidTemporaryPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That temporary password is invalid or has expired.",
        ) from exc
    # Restricted session: can only reach change-password.
    issued = session_service.create_session(db, user, kind=SessionKind.password_change)
    db.commit()
    _set_session_cookies(response, issued)
    return MeResponse(
        id=user.id, username=user.username, role=user.role, force_password_change=True
    )


@router.post("/change-password", response_model=MeResponse)
def change_password(
    payload: ChangePasswordBody,
    response: Response,
    resolved=Depends(require_csrf_any),
    db: DbSession = Depends(get_db),
) -> MeResponse:
    user = resolved.user
    forced = resolved.session.kind == SessionKind.password_change
    if not forced:
        # Normal change requires the current password.
        if not payload.current_password or not auth_service.verify_password(
            payload.current_password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect."
            )
    try:
        auth_service.set_new_password(db, user=user, new_password=payload.new_password)
    except PasswordPolicyError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    if forced:
        reset_service.complete_reset(db, user=user)
    # Rotate: revoke all sessions (incl. current) and issue a fresh full session.
    session_service.revoke_all_for_user(db, user.id)
    issued = session_service.create_session(db, user, kind=SessionKind.full)
    db.commit()
    _set_session_cookies(response, issued)
    return MeResponse(
        id=user.id, username=user.username, role=user.role, force_password_change=False
    )
