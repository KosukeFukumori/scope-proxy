from httpx import AsyncClient
from sqlmodel import Session, select

from app.auth.password import hash_password
from app.models.token import Token
from app.models.user import User


async def test_list_users_requires_authentication(client: AsyncClient) -> None:
    response = await client.get("/_admin/api/users")
    assert response.status_code == 401


async def test_list_users_returns_all_users(logged_in_client: AsyncClient, test_user: User, session: Session) -> None:
    other = User(email="other@example.com", password_hash=hash_password("otherpass123"))
    session.add(other)
    session.commit()

    response = await logged_in_client.get("/_admin/api/users")
    assert response.status_code == 200
    emails = {row["email"] for row in response.json()}
    assert emails == {test_user.email, "other@example.com"}


async def test_create_user(logged_in_client: AsyncClient, session: Session) -> None:
    response = await logged_in_client.post(
        "/_admin/api/users",
        json={"email": "new-user@example.com", "password": "newuserpass123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new-user@example.com"
    assert "password" not in body

    stored = session.exec(select(User).where(User.email == "new-user@example.com")).first()
    assert stored is not None


async def test_create_user_duplicate_email_conflicts(logged_in_client: AsyncClient, test_user: User) -> None:
    response = await logged_in_client.post(
        "/_admin/api/users",
        json={"email": test_user.email, "password": "whatever123"},
    )
    assert response.status_code == 409


async def test_delete_self_is_forbidden(logged_in_client: AsyncClient, test_user: User) -> None:
    response = await logged_in_client.delete(f"/_admin/api/users/{test_user.id}")
    assert response.status_code == 403


async def test_delete_unknown_user_returns_404(logged_in_client: AsyncClient) -> None:
    response = await logged_in_client.delete("/_admin/api/users/999999")
    assert response.status_code == 404


async def test_delete_user_revokes_owned_tokens(logged_in_client: AsyncClient, session: Session) -> None:
    other = User(email="other@example.com", password_hash=hash_password("otherpass123"))
    session.add(other)
    session.commit()
    session.refresh(other)
    assert other.id is not None

    token = Token(user_id=other.id, name="other-token", token_hash="deadbeef")
    session.add(token)
    session.commit()
    session.refresh(token)

    other_id = other.id
    token_id = token.id

    response = await logged_in_client.delete(f"/_admin/api/users/{other_id}")
    assert response.status_code == 204

    # The request was handled on a different Session instance, so expire this
    # session's identity map before re-reading the rows it touched.
    session.expire_all()

    assert session.exec(select(User).where(User.id == other_id)).first() is None

    refreshed_token = session.exec(select(Token).where(Token.id == token_id)).first()
    assert refreshed_token is not None
    assert refreshed_token.revoked_at is not None
