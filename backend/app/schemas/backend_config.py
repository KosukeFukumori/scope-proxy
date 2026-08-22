from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import AwareDatetimeModel


class BackendConfigUpsert(BaseModel):
    endpoint_url: HttpUrl
    openapi_url: HttpUrl
    # None resets to the SCHEMA_SYNC_INTERVAL_SECONDS env var default; 0 explicitly disables auto sync.
    schema_sync_interval_seconds: int | None = Field(default=None, ge=0)


class BackendConfigRead(AwareDatetimeModel):
    id: int
    endpoint_url: str
    openapi_url: str
    last_fetched_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
    schema_sync_interval_seconds: int | None
    # The interval actually in effect: schema_sync_interval_seconds if set, otherwise the env var default.
    effective_schema_sync_interval_seconds: int
    # True when the corresponding field is pinned by the ENDPOINT_URL / OPENAPI_URL
    # env var, meaning it cannot be changed through the dashboard.
    endpoint_url_locked: bool
    openapi_url_locked: bool


class BackendConfigEnvPresetRead(BaseModel):
    """The raw ENDPOINT_URL / OPENAPI_URL env var values, if set.

    Exposed separately from BackendConfigRead so the dashboard can pre-fill and
    disable a locked field even before any backend_config row exists.
    """

    endpoint_url: str | None
    openapi_url: str | None
