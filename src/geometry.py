from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence, TypedDict, cast

Point = tuple[float, float]


class PolygonGeoJSON(TypedDict):
  type: Literal["Polygon"]
  coordinates: list[list[list[float]]]


@dataclass
class Polygon:
  rings: list[list[Point]]

  def __post_init(self):
    if not self.rings:
      raise ValueError("Polygon must have at least one ring")

    for i, ring in enumerate(self.rings):
      if len(ring) < 4:
        raise ValueError(f"Ring {i} has fewer than 4 points (including closure)")
      if not self._is_closed(ring):
        raise ValueError(f"Ring {i} is not closed: first and last points differ")

  @staticmethod
  def _is_closed(ring: Sequence[Point]) -> bool:
    return ring[0] == ring[-1]

  def to_wkt(self) -> str:
    rings_wkt = (
      "(" + ", ".join(f"{format_point(p)}" for p in ring) + ")" for ring in self.rings
    )
    return "POLYGON (" + ", ".join(rings_wkt) + ")"

  @classmethod
  def parse_geojson(cls, polygon: PolygonGeoJSON) -> Polygon:
    if polygon["type"] != "Polygon":
      raise ValueError(f"Unsupported geometry type: {polygon['type']}")

    rings: list[list[Point]] = []
    for ring in polygon["coordinates"]:
      points = [cast(Point, tuple(map(float, p))) for p in ring]

      if len(points) < 4:
        raise ValueError("GeoJSON ring must contain at least 4 points")

      if points[0] != points[-1]:
        points.append(points[0])

      rings.append(points)

    return cls(rings)


def format_point(point: Point) -> str:
  return " ".join(map(str, point))
