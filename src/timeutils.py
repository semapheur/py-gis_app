from datetime import datetime, timedelta, timezone
from enum import Enum


class TimeUnit(Enum):
  SECONDS = 1
  MILLISECONDS = 1_000
  MICROSECONDS = 1_000_000
  NANOSECONDS = 1_000_000_000


EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def datetime_to_unix(dt: datetime, unit: TimeUnit = TimeUnit.MILLISECONDS) -> int:
  if dt.tzinfo is None:
    raise ValueError("datetime must be timezone-aware")
  delta = dt.astimezone(timezone.utc) - EPOCH

  total_seconds = delta.days * 86_400 + delta.seconds

  return total_seconds * unit.value + (delta.microseconds * unit.value) // 1_000_000


def unix_to_datetime(value: int, unit: TimeUnit = TimeUnit.MILLISECONDS) -> datetime:
  seconds, remainder = divmod(value, unit.value)
  microseconds = (remainder * 1_000_000) // unit.value

  return EPOCH + timedelta(seconds=seconds, microseconds=microseconds)
