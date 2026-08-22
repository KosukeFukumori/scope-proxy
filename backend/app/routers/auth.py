import logging

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.auth.password import hash_password, verify_password
from app.auth.rate_limiter import login_rate_limiter
from app.deps import CurrentUserDep, SessionDep
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordChangeRequest,
    SetupRequest,
    SetupStatus,
    UsernameChangeRequest,
    UserRead,
)

logger = logging.getLogger("scope_proxy")

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/setup/status", response_model=SetupStatus)
def setup_status(session: SessionDep) -> SetupStatus:
    needs_setup = session.exec(select(User)).first() is None
    return SetupStatus(needs_setup=needs_setup)


@router.post("/setup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def setup(payload: SetupRequest, request: Request, session: SessionDep) -> User:
    # Only usable while no account exists yet; once the first admin is created (via this
    # endpoint, or via ADMIN_USERNAME/ADMIN_PASSWORD_HASH at startup), it stays closed for good.
    if session.exec(select(User)).first() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Setup has already been completed")

    username = payload.username.strip()
    if not username or not payload.password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Username and password are required"
        )

    user = User(username=username, password_hash=hash_password(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)

    request.session["user_id"] = user.id
    return user


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, request: Request, session: SessionDep) -> User:
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"ip:{client_ip}"
    username_key = f"username:{payload.username.lower()}"

    if login_rate_limiter.is_blocked(ip_key) or login_rate_limiter.is_blocked(username_key):
        logger.warning(
            "Login blocked by rate limit for username=%s from ip=%s", payload.username, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = session.exec(select(User).where(User.username == payload.username)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(username_key)
        logger.warning("Failed login attempt for username=%s from ip=%s", payload.username, client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    login_rate_limiter.reset(ip_key)
    login_rate_limiter.reset(username_key)
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    session.add(current_user)
    session.commit()


@router.patch("/me/username", response_model=UserRead)
def change_username(payload: UsernameChangeRequest, session: SessionDep, current_user: CurrentUserDep) -> User:
    current_user.username = payload.username
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user
