from datetime import datetime

from pydantic import BaseModel


class SchemaSnapshotRead(BaseModel):
    id: int
    fetched_at: datetime
    spec_hash: str
    diff_summary: str
