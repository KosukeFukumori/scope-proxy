import logging

from fastapi import APIRouter, HTTPException, Request, status
from sqlmodel import select

from app.auth.password import verify_password
from app.auth.rate_limiter import login_rate_limiter
from app.deps import CurrentUserDep, SessionDep
from app.models.user import User
from app.schemas.auth import LoginRequest, UserRead

logger = logging.getLogger("scope_proxy")

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/login", response_model=UserRead)
def login(payload: LoginRequest, request: Request, session: SessionDep) -> User:
    client_ip = request.client.host if request.client else "unknown"
    ip_key = f"ip:{client_ip}"
    email_key = f"email:{payload.email.lower()}"

    if login_rate_limiter.is_blocked(ip_key) or login_rate_limiter.is_blocked(email_key):
        logger.warning(
            "Login blocked by rate limit for email=%s from ip=%s", payload.email, client_ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        login_rate_limiter.record_failure(ip_key)
        login_rate_limiter.record_failure(email_key)
        logger.warning("Failed login attempt for email=%s from ip=%s", payload.email, client_ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    login_rate_limiter.reset(ip_key)
    login_rate_limiter.reset(email_key)
    request.session["user_id"] = user.id
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, current_user: CurrentUserDep) -> None:
    request.session.clear()


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUserDep) -> User:
    return current_user
