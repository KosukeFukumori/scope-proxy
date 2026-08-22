from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.auth.password import hash_password
from app.deps import CurrentUserDep, SessionDep
from app.models.token import Token
from app.models.user import User
from app.schemas.user import UserCreate, UserSummary

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserSummary])
def list_users(session: SessionDep, current_user: CurrentUserDep) -> list[User]:
    return list(session.exec(select(User)).all())


@router.post("", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, session: SessionDep, current_user: CurrentUserDep) -> User:
    existing = session.exec(select(User).where(User.email == payload.email)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: SessionDep, current_user: CurrentUserDep) -> None:
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot delete your own account")

    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Cascade-revoke tokens owned by the deleted user instead of removing them,
    # so past usage records referencing these tokens remain intact.
    owned_tokens = session.exec(select(Token).where(Token.user_id == user_id)).all()
    for token in owned_tokens:
        if token.revoked_at is None:
            token.revoked_at = datetime.now(UTC)
            session.add(token)

    session.delete(user)
    session.commit()
