from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Token(SQLModel, table=True):
    __tablename__ = "tokens"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    token_hash: str = Field(unique=True, index=True)
    """SHA-256ハッシュ。生の値はDBに保存しない。"""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


class TokenPermission(SQLModel, table=True):
    """トークンとoperationの多対多関連。"""

    __tablename__ = "token_permissions"

    id: int | None = Field(default=None, primary_key=True)
    token_id: int = Field(foreign_key="tokens.id", index=True)
    operation_id: str = Field(foreign_key="operations.operation_id", index=True)
