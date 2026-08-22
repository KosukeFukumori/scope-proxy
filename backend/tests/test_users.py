from httpx import AsyncClient
from sqlmodel import Session, select

from app.models.token import Token
from app.models.user import User


async def test_list_users_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/users")
    assert response.status_code == 401


async def test_list_users(logged_in_client: AsyncClient, test_user: User) -> None:
    response = await logged_in_client.get("/_admin/api/users")
    assert response.status_code == 200
    emails = [user["email"] for user in response.json()]
    assert emails == [test_user.email]


async def test_create_user(logged_in_client: AsyncClient, session: Session) -> None:
    response = await logged_in_client.post(
        "/_admin/api/users",
        json={"email": "new-user@example.com", "password": "supersecret1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-user@example.com"
    assert "password" not in body
    assert "password_hash" not in body

    stored = session.exec(select(User).where(User.email == "new-user@example.com")).first()
    assert stored is not None


async def test_create_user_duplicate_email_fails(logged_in_client: AsyncClient, test_user: User) -> None:
    response = await logged_in_client.post(
        "/_admin/api/users",
        json={"email": test_user.email, "password": "supersecret1"},
    )
    assert response.status_code == 409


async def test_delete_self_is_forbidden(logged_in_client: AsyncClient, test_user: User) -> None:
    response = await logged_in_client.delete(f"/_admin/api/users/{test_user.id}")
    assert response.status_code == 403


async def test_delete_user_not_found(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.delete("/_admin/api/users/9999")
    assert response.status_code == 404


async def test_delete_user_revokes_owned_tokens(logged_in_client: AsyncClient, session: Session) -> None:
    create_response = await logged_in_client.post(
        "/_admin/api/users",
        json={"email": "other-user@example.com", "password": "supersecret1"},
    )
    other_user_id = create_response.json()["id"]

    session.add(Token(user_id=other_user_id, name="other-token", token_hash="hash-value"))
    session.commit()

    delete_response = await logged_in_client.delete(f"/_admin/api/users/{other_user_id}")
    assert delete_response.status_code == 204

    assert session.get(User, other_user_id) is None
    token = session.exec(select(Token).where(Token.user_id == other_user_id)).first()
    assert token is not None
    assert token.revoked_at is not None
