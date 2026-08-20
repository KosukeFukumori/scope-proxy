from fastapi import APIRouter, HTTPException, status

from app.deps import CurrentUserDep, SessionDep
from app.models.backend_config import BackendConfig
from app.schemas.backend_config import BackendConfigRead, BackendConfigUpsert

router = APIRouter(prefix="/api/backend-config", tags=["backend-config"])


def _get_singleton(session) -> BackendConfig | None:
    return session.get(BackendConfig, 1)


@router.get("", response_model=BackendConfigRead)
def get_backend_config(session: SessionDep, current_user: CurrentUserDep) -> BackendConfig:
    config = _get_singleton(session)
    if config is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Backend config not set")
    return config


@router.put("", response_model=BackendConfigRead)
def upsert_backend_config(
    payload: BackendConfigUpsert, session: SessionDep, current_user: CurrentUserDep
) -> BackendConfig:
    config = _get_singleton(session)
    if config is None:
        config = BackendConfig(id=1, endpoint_url=str(payload.endpoint_url), openapi_url=str(payload.openapi_url))
    else:
        config.endpoint_url = str(payload.endpoint_url)
        config.openapi_url = str(payload.openapi_url)

    session.add(config)
    session.commit()
    session.refresh(config)
    return config
