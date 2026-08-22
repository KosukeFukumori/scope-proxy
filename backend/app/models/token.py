from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Token(SQLModel, table=True):
    # sqlmodel declares __tablename__ as declared_attr; pyright cannot narrow a plain str assignment.
    __tablename__ = "tokens"  # type: ignore[assignment]

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    name: str
    token_hash: str = Field(unique=True, index=True)
    """SHA-256 hash. The raw value is never stored in the DB."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    revoked_at: datetime | None = None
    last_used_at: datetime | None = None


class TokenPermission(SQLModel, table=True):
    """Many-to-many association between tokens and operations."""

    # sqlmodel declares __tablename__ as declared_attr; pyright cannot narrow a plain str assignment.
    __tablename__ = "token_permissions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    token_id: str = Field(foreign_key="tokens.id", index=True)
    operation_id: str = Field(foreign_key="operations.operation_id", index=True)
