from datetime import datetime

from pydantic import BaseModel, HttpUrl


class BackendConfigUpsert(BaseModel):
    endpoint_url: HttpUrl
    openapi_url: HttpUrl


class BackendConfigRead(BaseModel):
    id: int
    endpoint_url: str
    openapi_url: str
    last_fetched_at: datetime | None
    last_sync_status: str | None
    last_sync_error: str | None
