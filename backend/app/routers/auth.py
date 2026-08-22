from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.auth.password import hash_password, verify_password
from app.deps import CurrentUserDep, SessionDep
from app.models.user import User
from app.schemas.auth import LoginRequest, PasswordChangeRequest, UserRead

router = APIRouter(prefix="/api", tags=["auth"])


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


@router.patch("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChangeRequest, session: SessionDep, current_user: CurrentUserDep) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    session.add(current_user)
    session.commit()
