import math
from typing import Sequence


def dot(a: Sequence[float], b: Sequence[float]) -> float:
  if len(a) != len(b):
    raise ValueError("a and b must have equal length")

  result = 0.0
  for i in range(len(a)):
    result += a[i] * b[i]

  return result


def norm(a: Sequence[float]) -> float:
  norm_squared = 0.0
  for i in a:
    norm_squared += i**2

  return math.sqrt(norm_squared)
