from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUserDep, SessionDep
from app.models.backend_config import BackendConfig
from app.models.schema_snapshot import SchemaSnapshot
from app.schemas.backend_config import BackendConfigRead, BackendConfigUpsert
from app.schemas.schema_snapshot import SchemaSnapshotRead
from app.services.schema_sync import (
    effective_sync_interval_seconds,
    refresh_backend_schema,
)

router = APIRouter(prefix="/api/backend-config", tags=["backend-config"])


def _get_singleton(session) -> BackendConfig | None:
    return session.get(BackendConfig, 1)


def _to_read(config: BackendConfig) -> BackendConfigRead:
    return BackendConfigRead(
        id=config.id,  # type: ignore[arg-type]
        endpoint_url=config.endpoint_url,
        openapi_url=config.openapi_url,
        last_fetched_at=config.last_fetched_at,
        last_sync_status=config.last_sync_status,
        last_sync_error=config.last_sync_error,
        schema_sync_interval_seconds=config.schema_sync_interval_seconds,
        effective_schema_sync_interval_seconds=effective_sync_interval_seconds(config),
    )


@router.get("", response_model=BackendConfigRead)
def get_backend_config(
    session: SessionDep, current_user: CurrentUserDep
) -> BackendConfigRead:
    config = _get_singleton(session)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backend config not set"
        )
    return _to_read(config)


@router.put("", response_model=BackendConfigRead)
def upsert_backend_config(
    payload: BackendConfigUpsert, session: SessionDep, current_user: CurrentUserDep
) -> BackendConfigRead:
    config = _get_singleton(session)
    if config is None:
        config = BackendConfig(
            id=1,
            endpoint_url=str(payload.endpoint_url),
            openapi_url=str(payload.openapi_url),
            schema_sync_interval_seconds=payload.schema_sync_interval_seconds,
        )
    else:
        config.endpoint_url = str(payload.endpoint_url)
        config.openapi_url = str(payload.openapi_url)
        config.schema_sync_interval_seconds = payload.schema_sync_interval_seconds

    session.add(config)
    session.commit()
    session.refresh(config)
    return _to_read(config)


@router.post("/refresh", response_model=SchemaSnapshotRead)
async def refresh_backend_config(
    session: SessionDep, current_user: CurrentUserDep
) -> SchemaSnapshot:
    config = _get_singleton(session)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backend config not set"
        )

    return await refresh_backend_schema(session, config)
