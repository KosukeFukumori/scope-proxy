from datetime import UTC, datetime

from pydantic import BaseModel, model_validator


class AwareDatetimeModel(BaseModel):
    """Base model that normalizes naive ``datetime`` fields to UTC-aware ones.

    SQLite doesn't preserve tzinfo, so values read back from the DB come out
    naive even though they are always stored as UTC. Without this, API
    responses mix naive values (from the DB) with aware ones (freshly created
    in memory), and clients that parse the naive form as local time end up
    off by the timezone offset. Treating every naive datetime as UTC before
    serialization keeps all responses consistent (`+00:00` / `Z` suffix).
    """

    @model_validator(mode="after")
    def _make_datetimes_aware(self) -> "AwareDatetimeModel":
        for field_name in self.__class__.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, datetime) and value.tzinfo is None:
                setattr(self, field_name, value.replace(tzinfo=UTC))
        return self
