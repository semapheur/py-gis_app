import re
from typing import Any, Callable

type Validator = Callable[[Any], None]


def min_value(n: float) -> Validator:
  def check(v):
    if v < n:
      raise ValueError(f"must be >= {n}, got {v}")

  check.sql = f"{{col}} >= {n}"  # type: ignore[attr-defined]
  return check


def max_value(n: float) -> Validator:
  def check(v):
    if v > n:
      raise ValueError(f"must be <= {n}, got {v}")

  check.sql = f"{{col}} <= {n}"  # type: ignore[attr-defined]
  return check


def max_length(n: int) -> Validator:
  def check(v):
    if len(v) > n:
      raise ValueError(f"length must be <= {n}, got {len(v)}")

  check.sql = f"length({{col}}) <= {n}"  # type: ignore[attr-defined]
  return check


def one_of(*allowed: Any) -> Validator:
  def check(v):
    if v not in allowed:
      raise ValueError(f"must be one of {allowed}, got {v!r}")

  quoted = ", ".join(
    "'" + a.replace("'", "''") + "'" if isinstance(a, str) else str(a) for a in allowed
  )
  check.sql = f"{{col}} IN ({quoted})"  # type: ignore[attr-defined]
  return check


def matches(pattern: str) -> Validator:
  rx = re.compile(pattern)

  def check(v):
    if not rx.fullmatch(v):
      raise ValueError(f"must match {pattern!r}, got {v!r}")

  return check
