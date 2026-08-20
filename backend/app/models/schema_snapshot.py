from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class SchemaSnapshot(SQLModel, table=True):
    __tablename__ = "schema_snapshots"

    id: int | None = Field(default=None, primary_key=True)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    spec_hash: str
    diff_summary: str
    """追加/削除/更新されたoperationIdの一覧をJSON文字列として保存する。"""
