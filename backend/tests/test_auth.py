from httpx import AsyncClient

from app.models.user import User


async def test_login_success(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/login",
        json={"email": test_user.email, "password": "testpass123"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": test_user.id, "email": test_user.email}


async def test_login_wrong_password(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/login",
        json={"email": test_user.email, "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_unknown_email(client: AsyncClient) -> None:
    response = await client.post(
        "/_admin/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == 401


async def test_logout_requires_authentication(client: AsyncClient) -> None:
    response = await client.post("/_admin/logout")
    assert response.status_code == 401


async def test_logout_invalidates_session(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.post("/_admin/logout")
    assert response.status_code == 204

    response = await logged_in_client.post("/_admin/logout")
    assert response.status_code == 401
