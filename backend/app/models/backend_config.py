from datetime import datetime

from sqlmodel import Field, SQLModel


class BackendConfig(SQLModel, table=True):
    """Configuration for the upstream server. Only a single record is used (managing multiple backends is out of scope)."""

    # sqlmodel declares __tablename__ as declared_attr; pyright cannot narrow a plain str assignment.
    __tablename__ = "backend_config"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    endpoint_url: str
    openapi_url: str
    last_fetched_at: datetime | None = None
    # Outcome of the most recent sync attempt (manual or scheduled): "success" or "error".
    last_sync_status: str | None = None
    # Error message from the most recent failed sync attempt, if any.
    last_sync_error: str | None = None
