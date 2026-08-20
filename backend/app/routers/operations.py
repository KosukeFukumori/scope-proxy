from fastapi import APIRouter, Query
from sqlmodel import select

from app.deps import CurrentUserDep, SessionDep
from app.models.operation import Operation
from app.schemas.operation import OperationRead

router = APIRouter(prefix="/api/operations", tags=["operations"])


@router.get("", response_model=list[OperationRead])
def list_operations(
    session: SessionDep,
    current_user: CurrentUserDep,
    is_active: bool | None = Query(default=None),
) -> list[Operation]:
    statement = select(Operation)
    if is_active is not None:
        statement = statement.where(Operation.is_active == is_active)
    return list(session.exec(statement).all())
