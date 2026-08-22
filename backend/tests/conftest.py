from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlmodel import Session, SQLModel, create_engine

from app.auth.password import hash_password
from app.auth.rate_limiter import login_rate_limiter
from app.db import get_session
from app.main import app
from app.models.user import User
from app.services.operation_matcher import reset_operation_matcher_cache


@pytest.fixture(autouse=True)
def reset_login_rate_limiter() -> Generator[None]:
    """The login rate limiter is a process-wide singleton, so its state must be
    reset between tests to avoid cross-test interference.
    """
    login_rate_limiter.clear()
    yield
    login_rate_limiter.clear()


@pytest.fixture
def engine(tmp_path: Path) -> Generator:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine) -> Generator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def _reset_operation_matcher_cache() -> Generator[None]:
    """Ensure the process-local OperationMatcher cache doesn't leak across tests."""
    reset_operation_matcher_cache()
    yield
    reset_operation_matcher_cache()


@pytest.fixture(autouse=True)
def override_get_session(engine):
    def _get_session_override() -> Generator[Session]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    yield
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(autouse=True)
async def backend_http_client() -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient() as http_client:
        app.state.http_client = http_client
        yield http_client


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    # Use an https:// base URL so the session cookie's Secure attribute (set via
    # SESSION_COOKIE_SECURE, default true) is actually stored and resent by the
    # httpx cookie jar between requests, matching real browser behavior.
    async with AsyncClient(transport=transport, base_url="https://testserver") as ac:
        yield ac


@pytest.fixture
def test_user(session: Session) -> User:
    user = User(username="testuser", password_hash=hash_password("testpass123"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest_asyncio.fixture
async def logged_in_client(client: AsyncClient, test_user: User) -> AsyncClient:
    response = await client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    assert response.status_code == 200
    return client
