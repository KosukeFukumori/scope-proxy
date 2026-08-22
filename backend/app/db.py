from collections.abc import Generator

from sqlalchemy import Engine
from sqlmodel import Session, create_engine, select

from app import (
    models,  # noqa: F401  needed to register tables on SQLModel.metadata (used in tests)
)
from app.config import settings
from app.migration_runner import run_migrations
from app.models.user import User

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)


def init_db() -> None:
    """Run migrations to bring the DB schema up to date, then bootstrap the
    initial admin user from ADMIN_USERNAME / ADMIN_PASSWORD_HASH if configured
    and no user exists yet.
    """
    run_migrations(engine)
    bootstrap_admin_user(engine, settings.admin_username, settings.admin_password_hash)


def bootstrap_admin_user(engine: Engine, admin_username: str | None, admin_password_hash: str | None) -> None:
    """Create the initial admin user from env-provided credentials.

    A no-op unless both values are set and no user exists yet. admin_password_hash
    must already be a bcrypt hash (see README), not a plaintext password.
    """
    if not (admin_username and admin_password_hash):
        return

    with Session(engine) as session:
        if session.exec(select(User)).first() is not None:
            return

        user = User(username=admin_username.strip(), password_hash=admin_password_hash)
        session.add(user)
        session.commit()


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
