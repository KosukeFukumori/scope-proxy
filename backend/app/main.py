import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.db import create_db_and_tables
from app.routers import (
    auth,
    backend_config,
    operations,
    proxy,
    schema_snapshots,
    tokens,
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
    create_db_and_tables()
    async with httpx.AsyncClient() as http_client:
        app.state.http_client = http_client
        yield


app = FastAPI(title="scope-proxy", lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(auth.router, prefix="/_admin")
app.include_router(backend_config.router, prefix="/_admin")
app.include_router(tokens.router, prefix="/_admin")
app.include_router(operations.router, prefix="/_admin")
app.include_router(schema_snapshots.router, prefix="/_admin")

if FRONTEND_DIST.is_dir():
    app.mount("/_admin", StaticFiles(directory=FRONTEND_DIST, html=True), name="admin-frontend")

# プロキシは全パスのcatch-allのため、必ず他のルーター・静的ファイルの登録後に最後へ追加する
app.include_router(proxy.router)
