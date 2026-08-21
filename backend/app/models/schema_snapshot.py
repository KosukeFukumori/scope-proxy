from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class SchemaSnapshot(SQLModel, table=True):
    __tablename__ = "schema_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    spec_hash: str
    diff_summary: str
    """Stores the list of added/removed/updated operationIds as a JSON string."""
