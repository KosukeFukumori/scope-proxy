import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import init_db
from app.routers import (
    auth,
    backend_config,
    health,
    operations,
    proxy,
    schema_snapshots,
    tokens,
    users,
)

logger = logging.getLogger("scope_proxy")

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    if settings.secret_key_is_generated:
        logger.warning(
            "SECRET_KEY is not set; a random key was generated for this process. "
            "Sessions will be invalidated on every restart. Set SECRET_KEY in .env for production use."
        )
    init_db()
    async with httpx.AsyncClient(timeout=settings.proxy_timeout_seconds) as http_client:
        app.state.http_client = http_client
        yield


app = FastAPI(title="scope-proxy", lifespan=lifespan)

assert settings.secret_key is not None  # generated in app.config if not set via env
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(health.router, prefix="/_admin")
app.include_router(auth.router, prefix="/_admin")
app.include_router(backend_config.router, prefix="/_admin")
app.include_router(tokens.router, prefix="/_admin")
app.include_router(operations.router, prefix="/_admin")
app.include_router(schema_snapshots.router, prefix="/_admin")
app.include_router(users.router, prefix="/_admin")

if FRONTEND_DIST.is_dir():

    @app.get("/_admin/{full_path:path}", include_in_schema=False)
    async def serve_frontend(full_path: str) -> Response:
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


# The proxy is a catch-all for every path, so it must always be registered last,
# after all other routers and static files.
app.include_router(proxy.router)
