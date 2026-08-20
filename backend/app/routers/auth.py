from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.auth.password import verify_password
from app.deps import CurrentUserDep, SessionDep
from app.models.user import User
from app.schemas.auth import LoginRequest, UserRead

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, request: Request, session: SessionDep) -> User:
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, current_user: CurrentUserDep) -> None:
    request.session.clear()


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUserDep) -> User:
    return current_user
