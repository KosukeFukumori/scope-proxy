import asyncio
import contextlib
import logging
import secrets
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import Settings, settings
from app.db import engine, init_db
from app.routers import (
    auth,
    backend_config,
    health,
    operations,
    proxy,
    schema_snapshots,
    tokens,
    usage,
    users,
)
from app.services.schema_sync import schema_sync_loop

# uvicorn only attaches handlers to its own "uvicorn"/"uvicorn.error"/"uvicorn.access"
# loggers, not the root logger, so app loggers (e.g. "scope_proxy",
# "app.migration_runner") would otherwise be dropped by logging's lastResort
# handler (WARNING+ only). Configure the root logger explicitly so INFO logs
# from application code show up in `docker compose logs`.
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

logger = logging.getLogger("scope_proxy")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application.

    Accepts an explicit `Settings` instance so tests can exercise the app with
    settings other than the process-wide singleton (e.g. CORS enabled/disabled).
    """
    app_settings = app_settings if app_settings is not None else settings

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        if app_settings.secret_key_is_generated:
            logger.warning(
                "SECRET_KEY is not set; a random key was generated for this process. "
                "Sessions will be invalidated on every restart. Set SECRET_KEY in .env for production use."
            )
        init_db()

        # Always runs; the configured interval (0 = disabled) is re-read from backend_config on
        # every tick, so it reacts to changes made from the GUI without needing a restart.
        sync_task = asyncio.create_task(schema_sync_loop(engine))

        async with httpx.AsyncClient(timeout=app_settings.proxy_timeout_seconds) as http_client:
            app.state.http_client = http_client
            yield

        sync_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await sync_task

    app = FastAPI(title="scope-proxy", lifespan=lifespan)

    # Fall back to a freshly generated key when the caller didn't provide one
    # (mirrors the generation the process-wide `settings` singleton does at import time).
    secret_key = app_settings.secret_key or secrets.token_urlsafe(32)
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        session_cookie=app_settings.session_cookie_name,
        same_site="lax",
        https_only=app_settings.session_cookie_secure,
        max_age=app_settings.session_cookie_max_age,
    )

    # CORS is disabled by default (empty allowlist): every request, including
    # preflight OPTIONS, then falls through to the normal auth flow and is denied
    # without a bearer token. When origins are configured, CORSMiddleware is added
    # last so it becomes the outermost layer and short-circuits preflight OPTIONS
    # requests before they ever reach SessionMiddleware or the routes/auth logic.
    cors_origins = app_settings.cors_allowed_origins_list
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(health.router, prefix="/_admin")
    app.include_router(auth.router, prefix="/_admin")
    app.include_router(backend_config.router, prefix="/_admin")
    app.include_router(tokens.router, prefix="/_admin")
    app.include_router(operations.router, prefix="/_admin")
    app.include_router(schema_snapshots.router, prefix="/_admin")
    app.include_router(usage.router, prefix="/_admin")
    app.include_router(users.router, prefix="/_admin")

    if FRONTEND_DIST.is_dir():

        async def serve_frontend(full_path: str = "") -> Response:
            """Serve the frontend SPA. Returns the actual file if it exists,
            otherwise falls back to index.html (for react-router client-side routes).
            """
            candidate = (FRONTEND_DIST / full_path).resolve()
            if full_path and candidate.is_file() and FRONTEND_DIST in candidate.parents:
                return FileResponse(candidate)

            index_file = FRONTEND_DIST / "index.html"
            if not index_file.is_file():
                raise HTTPException(status_code=404)
            return FileResponse(index_file)

        # Without this, "/_admin" (no trailing slash) falls through to the
        # proxy's catch-all route below instead of matching "/_admin/{full_path}".
        app.add_api_route("/_admin", serve_frontend, include_in_schema=False)
        app.add_api_route("/_admin/{full_path:path}", serve_frontend, include_in_schema=False)

    # The proxy is a catch-all for every path, so it must always be registered last,
    # after all other routers and static files.
    app.include_router(proxy.router)

    return app


app = create_app()
