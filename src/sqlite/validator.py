def min_value(n):
  def check(v):
    if v < n:
      raise ValueError(f"must be >= {n}, got {v}")

  return check


def max_length(n):
  def check(v):
    if len(v) > n:
      raise ValueError(f"length must be <= {n}, got {len(v)}")

  return check


def one_of(*allowed):
  def check(v):
    if v not in allowed:
      raise ValueError(f"must be one of {allowed}, got {v!r}")

  return check


def matches(pattern):
  import re

  rx = re.compile(pattern)

  def check(v):
    if not rx.fullmatch(v):
      raise ValueError(f"must match {pattern!r}, got {v!r}")

  return check
