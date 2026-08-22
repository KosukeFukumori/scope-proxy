from httpx import AsyncClient
from sqlmodel import Session

from app.auth.password import verify_password
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


async def test_change_password_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch(
        "/_admin/api/me/password",
        json={"current_password": "testpass123", "new_password": "newpassword1"},
    )
    assert response.status_code == 401


async def test_change_password_success(logged_in_client: AsyncClient, test_user: User, session: Session) -> None:
    response = await logged_in_client.patch(
        "/_admin/api/me/password",
        json={"current_password": "testpass123", "new_password": "newpassword1"},
    )
    assert response.status_code == 204

    session.refresh(test_user)
    assert verify_password("newpassword1", test_user.password_hash)


async def test_change_password_wrong_current_password(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.patch(
        "/_admin/api/me/password",
        json={"current_password": "wrong-password", "new_password": "newpassword1"},
    )
    assert response.status_code == 400


async def test_change_password_too_short(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.patch(
        "/_admin/api/me/password",
        json={"current_password": "testpass123", "new_password": "short"},
    )
    assert response.status_code == 422
