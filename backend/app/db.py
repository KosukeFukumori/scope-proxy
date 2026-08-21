from collections.abc import Generator

from sqlmodel import Session, create_engine

from app import (
    models,  # noqa: F401  needed to register tables on SQLModel.metadata (used in tests)
)
from app.config import settings
from app.migration_runner import run_migrations

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)


def init_db() -> None:
    """Run migrations to bring the DB schema up to date."""
    run_migrations(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
