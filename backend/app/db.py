from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  テーブルメタデータ登録のため必要
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
