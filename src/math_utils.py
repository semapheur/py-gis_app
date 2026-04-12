import math
from typing import Sequence, TypeAlias

Vec3: TypeAlias = tuple[float, float, float]


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


def ground_sample_distance(
  sample_spacing: float, unit_vector: Vec3, point: Vec3
) -> float:
  n_mag = norm(point)
  surface_normal = (point[0] / n_mag, point[1] / n_mag, point[2] / n_mag)
  udotn = dot(unit_vector, surface_normal)
  ground_factor = math.sqrt(1.0 - udotn**2)

  return sample_spacing * ground_factor
