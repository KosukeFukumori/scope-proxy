from fastapi import APIRouter
from sqlmodel import select

from app.deps import CurrentUserDep, SessionDep
from app.models.schema_snapshot import SchemaSnapshot
from app.schemas.schema_snapshot import SchemaSnapshotRead

router = APIRouter(prefix="/api/schema-snapshots", tags=["schema-snapshots"])


@router.get("", response_model=list[SchemaSnapshotRead])
def list_schema_snapshots(session: SessionDep, current_user: CurrentUserDep) -> list[SchemaSnapshot]:
    statement = select(SchemaSnapshot).order_by(SchemaSnapshot.fetched_at.desc())
    return list(session.exec(statement).all())
