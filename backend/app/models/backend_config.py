from datetime import datetime

from sqlmodel import Field, SQLModel


class BackendConfig(SQLModel, table=True):
    """Configuration for the upstream server. Only a single record is used (managing multiple backends is out of scope)."""

    __tablename__ = "backend_config"

    id: int | None = Field(default=None, primary_key=True)
    endpoint_url: str
    openapi_url: str
    last_fetched_at: datetime | None = None
