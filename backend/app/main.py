from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
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

# プロキシは全パスのcatch-allのため、必ず他のルーター登録後に最後へ追加する
app.include_router(proxy.router)
