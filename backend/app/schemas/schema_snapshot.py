from datetime import datetime

from app.schemas.common import AwareDatetimeModel


class SchemaSnapshotRead(AwareDatetimeModel):
    id: int
    fetched_at: datetime
    spec_hash: str
    diff_summary: str
