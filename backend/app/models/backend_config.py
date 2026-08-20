from datetime import datetime

from sqlmodel import Field, SQLModel


class BackendConfig(SQLModel, table=True):
    """接続先サーバーの設定。単一レコードのみ運用する(スコープ外: 複数バックエンド管理)。"""

    __tablename__ = "backend_config"

    id: int | None = Field(default=None, primary_key=True)
    endpoint_url: str
    openapi_url: str
    last_fetched_at: datetime | None = None
