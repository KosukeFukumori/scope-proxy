from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete
from sqlmodel import Session

from app.config import settings
from app.deps import CurrentUserDep, SessionDep
from app.models.backend_config import BackendConfig
from app.models.operation import Operation
from app.models.token import TokenPermission
from app.schemas.backend_config import (
    BackendConfigEnvPresetRead,
    BackendConfigRead,
    BackendConfigUpsert,
)
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
        endpoint_url_locked=settings.endpoint_url is not None,
        openapi_url_locked=settings.openapi_url is not None,
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


def apply_env_config_overrides(session: Session) -> None:
    """Enforce ENDPOINT_URL / OPENAPI_URL presets in backend_config at startup.

    Only touches the fields that have an env var set; the other field (if any)
    keeps whatever was last saved through the dashboard. If neither the preset
    field(s) alone are enough to create a brand-new row (backend_config requires
    both URLs), the row is left absent until an admin supplies the missing URL
    through the dashboard -- at which point the locked field is still forced to
    the env value by upsert_backend_config.
    """
    if settings.endpoint_url is None and settings.openapi_url is None:
        return

    config = _get_singleton(session)
    if config is None:
        if settings.endpoint_url is None or settings.openapi_url is None:
            return
        config = BackendConfig(id=1, endpoint_url=settings.endpoint_url, openapi_url=settings.openapi_url)
        session.add(config)
        session.commit()
        return

    endpoint_url = settings.endpoint_url or config.endpoint_url
    openapi_url = settings.openapi_url or config.openapi_url
    url_changed = config.endpoint_url != endpoint_url or config.openapi_url != openapi_url
    if url_changed:
        _reset_operations_and_permissions(session)
        config.last_fetched_at = None
    config.endpoint_url = endpoint_url
    config.openapi_url = openapi_url
    session.add(config)
    session.commit()


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
    # A field pinned by ENDPOINT_URL / OPENAPI_URL always wins over the request
    # payload, regardless of what the client sends: the dashboard disables the
    # corresponding input, but this is the actual enforcement point.
    endpoint_url = settings.endpoint_url or str(payload.endpoint_url)
    openapi_url = settings.openapi_url or str(payload.openapi_url)

    config = _get_singleton(session)
    if config is None:
        config = BackendConfig(
            id=1,
            endpoint_url=endpoint_url,
            openapi_url=openapi_url,
            schema_sync_interval_seconds=payload.schema_sync_interval_seconds,
        )
    else:
        url_changed = config.endpoint_url != endpoint_url or config.openapi_url != openapi_url
        if url_changed:
            _reset_operations_and_permissions(session)
            config.last_fetched_at = None
        config.endpoint_url = endpoint_url
        config.openapi_url = openapi_url
        config.schema_sync_interval_seconds = payload.schema_sync_interval_seconds

    session.add(config)
    session.commit()
    session.refresh(config)
    return _to_read(config)


@router.get("/env-preset", response_model=BackendConfigEnvPresetRead)
def get_backend_config_env_preset(current_user: CurrentUserDep) -> BackendConfigEnvPresetRead:
    return BackendConfigEnvPresetRead(
        endpoint_url=settings.endpoint_url,
        openapi_url=settings.openapi_url,
    )


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
