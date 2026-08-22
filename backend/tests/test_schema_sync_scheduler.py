import asyncio

import httpx
import respx
from httpx import Response
from sqlmodel import Session

from app.models.backend_config import BackendConfig
from app.services.schema_sync import run_scheduled_sync, schema_sync_loop

OPENAPI_URL = "https://api.example.com/openapi.json"

SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "t", "version": "1"},
    "paths": {
        "/users": {
            "get": {"operationId": "listUsers", "responses": {"200": {"description": "ok"}}},
        },
    },
}


async def test_run_scheduled_sync_skips_when_backend_config_not_set(engine) -> None:
    # Should return without raising when no BackendConfig row exists yet.
    await run_scheduled_sync(engine)


@respx.mock
async def test_run_scheduled_sync_updates_status_on_success(engine) -> None:
    with Session(engine) as session:
        session.add(BackendConfig(id=1, endpoint_url="https://api.example.com", openapi_url=OPENAPI_URL))
        session.commit()

    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC))
    await run_scheduled_sync(engine)

    with Session(engine) as session:
        config = session.get(BackendConfig, 1)
        assert config is not None
        assert config.last_sync_status == "success"
        assert config.last_sync_error is None
        assert config.last_fetched_at is not None


@respx.mock
async def test_run_scheduled_sync_records_error_and_does_not_raise(engine) -> None:
    with Session(engine) as session:
        session.add(BackendConfig(id=1, endpoint_url="https://api.example.com", openapi_url=OPENAPI_URL))
        session.commit()

    respx.get(OPENAPI_URL).mock(side_effect=httpx.ConnectError("connection failed"))

    # Must not raise: the scheduled loop should keep running even when a sync attempt fails.
    await run_scheduled_sync(engine)

    with Session(engine) as session:
        config = session.get(BackendConfig, 1)
        assert config is not None
        assert config.last_sync_status == "error"
        assert config.last_sync_error is not None
        assert "connection failed" in config.last_sync_error


@respx.mock
async def test_schema_sync_loop_runs_periodically_until_cancelled(engine) -> None:
    with Session(engine) as session:
        session.add(BackendConfig(id=1, endpoint_url="https://api.example.com", openapi_url=OPENAPI_URL))
        session.commit()

    respx.get(OPENAPI_URL).mock(return_value=Response(200, json=SPEC))

    task = asyncio.create_task(schema_sync_loop(engine, interval_seconds=0.01))
    await asyncio.sleep(0.05)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    with Session(engine) as session:
        config = session.get(BackendConfig, 1)
        assert config is not None
        assert config.last_sync_status == "success"
        # The loop should have run more than once within the sleep window.
        assert respx.calls.call_count >= 2
