from httpx import AsyncClient

from app.config import settings
from app.models.user import User


async def test_setup_status_needs_setup_when_no_user(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/setup/status")
    assert response.status_code == 200
    assert response.json() == {"needs_setup": True}


async def test_setup_status_does_not_need_setup_once_user_exists(client: AsyncClient, test_user: User) -> None:
    response = await client.get("/_admin/api/setup/status")
    assert response.status_code == 200
    assert response.json() == {"needs_setup": False}


async def test_setup_creates_user_and_logs_in(client: AsyncClient) -> None:
    response = await client.post(
        "/_admin/api/setup",
        json={"username": "admin", "password": "initial-pass123"},
    )
    assert response.status_code == 201
    assert response.json()["username"] == "admin"

    # The setup call also establishes a session, like /login does.
    me_response = await client.get("/_admin/api/me")
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "admin"


async def test_setup_rejected_once_a_user_exists(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/api/setup",
        json={"username": "another-admin", "password": "whatever123"},
    )
    assert response.status_code == 409


async def test_login_success(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": test_user.id, "username": test_user.username}


async def test_login_wrong_password(client: AsyncClient, test_user: User) -> None:
    response = await client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "wrong-password"},
    )
    assert response.status_code == 401


async def test_login_unknown_username(client: AsyncClient) -> None:
    response = await client.post(
        "/_admin/api/login",
        json={"username": "nobody", "password": "whatever"},
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
    assert response.json() == {"id": test_user.id, "username": test_user.username}


async def test_change_password_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch(
        "/_admin/api/me/password",
        json={"current_password": "testpass123", "new_password": "newpass456"},
    )
    assert response.status_code == 401


async def test_change_password_wrong_current_password(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.patch(
        "/_admin/api/me/password",
        json={"current_password": "wrong-password", "new_password": "newpass456"},
    )
    assert response.status_code == 401


async def test_change_password_success_allows_login_with_new_password(
    logged_in_client: AsyncClient, test_user: User
) -> None:
    response = await logged_in_client.patch(
        "/_admin/api/me/password",
        json={"current_password": "testpass123", "new_password": "newpass456"},
    )
    assert response.status_code == 204

    # The old session should no longer be able to log in with the old password.
    old_login = await logged_in_client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    assert old_login.status_code == 401

    new_login = await logged_in_client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "newpass456"},
    )
    assert new_login.status_code == 200


async def test_change_username_requires_authentication(client: AsyncClient) -> None:
    response = await client.patch(
        "/_admin/api/me/username",
        json={"username": "newname"},
    )
    assert response.status_code == 401


async def test_change_username_success_allows_login_with_new_username(
    logged_in_client: AsyncClient, test_user: User
) -> None:
    response = await logged_in_client.patch(
        "/_admin/api/me/username",
        json={"username": "newname"},
    )
    assert response.status_code == 200
    assert response.json() == {"id": test_user.id, "username": "newname"}

    old_login = await logged_in_client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    assert old_login.status_code == 401

    new_login = await logged_in_client.post(
        "/_admin/api/login",
        json={"username": "newname", "password": "testpass123"},
    )
    assert new_login.status_code == 200


async def test_login_blocked_after_repeated_failures(client: AsyncClient, test_user: User) -> None:
    """After enough failed attempts within the rate-limit window, the endpoint
    should return 429 instead of continuing to check the password.
    """
    for _ in range(settings.login_rate_limit_max_attempts):
        response = await client.post(
            "/_admin/api/login",
            json={"username": test_user.username, "password": "wrong-password"},
        )
        assert response.status_code == 401

    response = await client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "wrong-password"},
    )
    assert response.status_code == 429

    # Even the correct password should be blocked while the rate limit is active.
    response = await client.post(
        "/_admin/api/login",
        json={"username": test_user.username, "password": "testpass123"},
    )
    assert response.status_code == 429
