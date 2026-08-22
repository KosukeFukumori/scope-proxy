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
