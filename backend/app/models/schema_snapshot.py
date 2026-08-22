from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class SchemaSnapshot(SQLModel, table=True):
    # sqlmodel declares __tablename__ as declared_attr; pyright cannot narrow a plain str assignment.
    __tablename__ = "schema_snapshots"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    spec_hash: str
    diff_summary: str
    """Stores the list of added/removed/updated operationIds as a JSON string."""
