"""FastAPI application entrypoint.

Serves the versioned ``/api/v1`` API and, when present, the compiled frontend
static files from ``src/static`` (single-process deployment).
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .api.auth import router as auth_router
from .api.admin_users import router as admin_users_router
from .api.admin_reset import router as admin_reset_router
from .api.locations import router as locations_router
from .api.catalog import router as catalog_router
from .api.browse import router as browse_router
from .api.loans import router as loans_router
from .api.dashboard import router as dashboard_router
from .api.borrowers import router as borrowers_router
from .api.audit import router as audit_router
from .core.db import enforce_encryption_at_rest
from .core.schema import create_all

logger = logging.getLogger("library")

app = FastAPI(title="Library — Auth, Roles & User Management", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    # Fail closed if encryption at rest is required but unavailable (FR-030).
    enforce_encryption_at_rest()
    # Self-initializing: make sure the tables exist so a missing schema can never
    # surface as a 500 to the user (suits the local, low-maintenance deployment).
    create_all()


@app.exception_handler(Exception)
async def _unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    # Never leak a raw stack trace to the client; log it and return a clean,
    # user-facing message.
    logger.exception("Unhandled server error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Something went wrong on our end. Please try again."},
    )


# Versioned API: every route is exposed under /api/v1.
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_users_router, prefix="/api/v1")
app.include_router(admin_reset_router, prefix="/api/v1")
app.include_router(locations_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(browse_router, prefix="/api/v1")
app.include_router(loans_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(borrowers_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# Serve the compiled SPA if it has been built.
_static_dir = Path(__file__).parent / "static"
_assets_dir = _static_dir / "assets"
_index_file = _static_dir / "index.html"

# Real build assets are served from /assets.
if _assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")

if _index_file.is_file():
    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str):
        # Client-side routes (e.g. /login, /users) must return index.html so the
        # React router can handle them on a full page load or refresh. API and
        # health paths still return a proper JSON 404 instead of HTML.
        if full_path.startswith("api/") or full_path == "healthz":
            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(str(_index_file))
