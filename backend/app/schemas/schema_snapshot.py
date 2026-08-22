from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import AwareDatetimeModel


class SchemaSnapshotRead(AwareDatetimeModel):
    id: int
    fetched_at: datetime
    spec_hash: str
    diff_summary: str


class SchemaRefreshRead(BaseModel):
    """Response of a manual schema refresh.

    `diff_summary` is the diff of THIS refresh run. It can differ from
    `snapshot.diff_summary`: when the spec is unchanged, the returned snapshot is
    the (deduplicated) latest one whose diff belongs to an older run.
    """

    snapshot: SchemaSnapshotRead
    diff_summary: str
