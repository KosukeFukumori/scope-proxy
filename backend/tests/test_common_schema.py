from datetime import UTC, datetime

from app.schemas.common import AwareDatetimeModel

# Intentionally naive (no tzinfo) to exercise the UTC-normalization behavior under test.
NAIVE_VALUE = datetime(2026, 8, 21, 5, 0, 0)  # noqa: DTZ001


class _Sample(AwareDatetimeModel):
    value: datetime
    optional_value: datetime | None = None


def test_naive_datetime_is_normalized_to_utc_aware() -> None:
    model = _Sample(value=NAIVE_VALUE)
    assert model.value.tzinfo is not None
    offset = model.value.utcoffset()
    assert offset is not None
    assert offset.total_seconds() == 0


def test_aware_datetime_is_left_unchanged() -> None:
    aware = NAIVE_VALUE.replace(tzinfo=UTC)
    model = _Sample(value=aware)
    assert model.value == aware


def test_none_optional_datetime_stays_none() -> None:
    model = _Sample(value=NAIVE_VALUE, optional_value=None)
    assert model.optional_value is None


def test_serialized_output_includes_utc_offset() -> None:
    model = _Sample(value=NAIVE_VALUE)
    dumped = model.model_dump_json()
    assert "Z" in dumped or "+00:00" in dumped
