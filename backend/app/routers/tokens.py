from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.deps import CurrentUserDep, SessionDep
from app.models.token import Token, TokenPermission
from app.schemas.token import (
    TokenCreate,
    TokenCreateResponse,
    TokenDetailRead,
    TokenRead,
    TokenUpdate,
)
from app.services.token_service import generate_token

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


def _get_owned_token(session: SessionDep, current_user: CurrentUserDep, token_id: str) -> Token:
    token = session.get(Token, token_id)
    if token is None or token.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    return token


def _operation_ids(session: SessionDep, token_id: str) -> list[str]:
    rows = session.exec(select(TokenPermission.operation_id).where(TokenPermission.token_id == token_id)).all()
    return list(rows)


def _set_permissions(session: SessionDep, token_id: str, operation_ids: list[str]) -> None:
    existing = session.exec(select(TokenPermission).where(TokenPermission.token_id == token_id)).all()
    for row in existing:
        session.delete(row)
    for operation_id in operation_ids:
        session.add(TokenPermission(token_id=token_id, operation_id=operation_id))


@router.get("", response_model=list[TokenRead])
def list_tokens(session: SessionDep, current_user: CurrentUserDep) -> list[Token]:
    return list(session.exec(select(Token).where(Token.user_id == current_user.id)).all())


@router.post("", response_model=TokenCreateResponse, status_code=status.HTTP_201_CREATED)
def create_token(payload: TokenCreate, session: SessionDep, current_user: CurrentUserDep) -> TokenCreateResponse:
    raw, token_hash = generate_token()
    token = Token(
        user_id=current_user.id,
        name=payload.name,
        token_hash=token_hash,
        expires_at=payload.expires_at,
    )
    session.add(token)
    session.commit()
    session.refresh(token)

    _set_permissions(session, token.id, payload.operation_ids)
    session.commit()

    return TokenCreateResponse(
        id=token.id,
        name=token.name,
        created_at=token.created_at,
        expires_at=token.expires_at,
        revoked_at=token.revoked_at,
        last_used_at=token.last_used_at,
        operation_ids=payload.operation_ids,
        raw_token=raw,
    )


@router.get("/{token_id}", response_model=TokenDetailRead)
def get_token(token_id: str, session: SessionDep, current_user: CurrentUserDep) -> TokenDetailRead:
    token = _get_owned_token(session, current_user, token_id)
    return TokenDetailRead(
        id=token.id,
        name=token.name,
        created_at=token.created_at,
        expires_at=token.expires_at,
        revoked_at=token.revoked_at,
        last_used_at=token.last_used_at,
        operation_ids=_operation_ids(session, token_id),
    )


@router.patch("/{token_id}", response_model=TokenDetailRead)
def update_token(
    token_id: str, payload: TokenUpdate, session: SessionDep, current_user: CurrentUserDep
) -> TokenDetailRead:
    token = _get_owned_token(session, current_user, token_id)

    # Only fields explicitly present in the request body are applied.
    # This distinguishes "field omitted (no change)" from "field set to null
    # (clear the value)", so `expires_at: null` clears the expiration instead
    # of being silently ignored.
    update_fields = payload.model_dump(exclude_unset=True)

    if "name" in update_fields and update_fields["name"] is not None:
        token.name = update_fields["name"]
    if "expires_at" in update_fields:
        token.expires_at = update_fields["expires_at"]
    session.add(token)

    if "operation_ids" in update_fields and update_fields["operation_ids"] is not None:
        _set_permissions(session, token_id, update_fields["operation_ids"])

    session.commit()

    return TokenDetailRead(
        id=token.id,
        name=token.name,
        created_at=token.created_at,
        expires_at=token.expires_at,
        revoked_at=token.revoked_at,
        last_used_at=token.last_used_at,
        operation_ids=_operation_ids(session, token_id),
    )


@router.post("/{token_id}/revoke", response_model=TokenRead)
def revoke_token(token_id: str, session: SessionDep, current_user: CurrentUserDep) -> Token:
    token = _get_owned_token(session, current_user, token_id)
    if token.revoked_at is None:
        token.revoked_at = datetime.now(UTC)
        session.add(token)
        session.commit()
        session.refresh(token)
    return token
