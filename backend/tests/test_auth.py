from httpx import AsyncClient

from app.config import settings
from app.models.user import User


async def test_login_success(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/api/login",
        json={"email": test_user.email, "password": "testpass123"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": test_user.id, "email": test_user.email}


async def test_login_wrong_password(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/api/login",
        json={"email": test_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/_admin/api/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


async def test_logout_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/_admin/api/logout")
    assert response.status_code == 401


async def test_logout_invalidates_session(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.post("/_admin/api/logout")
    assert response.status_code == 204

    response = await logged_in_client.post("/_admin/api/logout")
    assert response.status_code == 401


async def test_me_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/me")
    assert response.status_code == 401


async def test_me_returns_current_user(logged_in_client: AsyncClient, test_user: User) -> None:
    response = await logged_in_client.get("/_admin/api/me")
    assert response.status_code == 200
    assert response.json() == {"id": test_user.id, "email": test_user.email}


async def test_login_blocked_after_repeated_failures(client: AsyncClient, test_user: User) -> None:
    """After enough failed attempts within the rate-limit window, the endpoint
    should return 429 instead of continuing to check the password.
    """
    for _ in range(settings.login_rate_limit_max_attempts):
        response = await client.post(
            "/_admin/api/login",
            json={"email": test_user.email, "password": "wrong-password"},
        )
        assert response.status_code == 401

    response = await client.post(
        "/_admin/api/login",
        json={"email": test_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 429

    # Even the correct password should be blocked while the rate limit is active.
    response = await client.post(
        "/_admin/api/login",
        json={"email": test_user.email, "password": "testpass123"},
    )
    assert response.status_code == 429
