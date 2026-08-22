from fastapi import APIRouter
from sqlalchemy import desc
from sqlmodel import select

from app.deps import CurrentUserDep, SessionDep
from app.models.schema_snapshot import SchemaSnapshot
from app.schemas.schema_snapshot import SchemaSnapshotRead

router = APIRouter(prefix="/api/schema-snapshots", tags=["schema-snapshots"])


@router.get("", response_model=list[SchemaSnapshotRead])
def list_schema_snapshots(session: SessionDep, current_user: CurrentUserDep) -> list[SchemaSnapshot]:
    # sqlmodel field access is statically typed as `datetime`, not a Column, so pyright
    # cannot see that this is actually a SQLAlchemy InstrumentedAttribute at runtime.
    statement = select(SchemaSnapshot).order_by(desc(SchemaSnapshot.fetched_at))  # type: ignore[arg-type]
    return list(session.exec(statement).all())
