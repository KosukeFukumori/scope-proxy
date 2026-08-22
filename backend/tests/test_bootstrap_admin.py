from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlmodel import Session, SQLModel, select

from app.auth.password import hash_password, verify_password
from app.db import bootstrap_admin_user
from app.models.user import User


@pytest.fixture
def engine(tmp_path: Path) -> Generator[Engine]:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


def test_bootstrap_creates_user_from_env_hash(engine: Engine) -> None:
    password_hash = hash_password("s3cret-pass")

    bootstrap_admin_user(engine, "admin", password_hash)

    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == "admin")).first()
        assert user is not None
        assert verify_password("s3cret-pass", user.password_hash)


def test_bootstrap_is_noop_when_env_vars_missing(engine: Engine) -> None:
    bootstrap_admin_user(engine, None, None)
    bootstrap_admin_user(engine, "admin", None)
    bootstrap_admin_user(engine, None, "some-hash")

    with Session(engine) as session:
        assert session.exec(select(User)).first() is None


def test_bootstrap_does_not_overwrite_existing_user(engine: Engine) -> None:
    with Session(engine) as session:
        session.add(User(username="existing", password_hash=hash_password("original")))
        session.commit()

    bootstrap_admin_user(engine, "admin", hash_password("new-pass"))

    with Session(engine) as session:
        users = session.exec(select(User)).all()
        assert len(users) == 1
        assert users[0].username == "existing"
