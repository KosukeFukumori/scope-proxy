from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete

from app.deps import CurrentUserDep, SessionDep
from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.token import TokenPermission
from app.schemas.backend_config import BackendConfigRead, BackendConfigUpsert
from app.schemas.schema_snapshot import SchemaRefreshRead, SchemaSnapshotRead
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


def _reset_operations_and_permissions(session) -> None:
    """Wipe operations and token permissions.

    Called when the upstream backend URL changes: permissions granted against the
    previous backend must never silently apply to a different server, even if it
    exposes operations with identical method/path/operationId (and thus identical
    hash ids). The admin re-syncs the schema and re-grants permissions explicitly.
    """
    session.execute(delete(TokenPermission))
    session.execute(delete(Operation))


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
        url_changed = config.endpoint_url != str(payload.endpoint_url) or config.openapi_url != str(
            payload.openapi_url
        )
        if url_changed:
            _reset_operations_and_permissions(session)
            config.last_fetched_at = None
        config.endpoint_url = str(payload.endpoint_url)
        config.openapi_url = str(payload.openapi_url)
        config.schema_sync_interval_seconds = payload.schema_sync_interval_seconds

    session.add(config)
    session.commit()
    session.refresh(config)
    return _to_read(config)


@router.post("/refresh", response_model=SchemaRefreshRead)
async def refresh_backend_config(session: SessionDep, current_user: CurrentUserDep) -> SchemaRefreshRead:
    config = _get_singleton(session)
    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backend config not set"
        )

    outcome = await refresh_backend_schema(session, config)
    return SchemaRefreshRead(
        snapshot=SchemaSnapshotRead.model_validate(outcome.snapshot.model_dump()),
        diff_summary=outcome.result.to_diff_summary(),
    )
