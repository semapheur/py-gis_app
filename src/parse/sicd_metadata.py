from datetime import datetime as dt
from typing import Sequence, Union

from src.parse.sicd_model import ImageCorner, LatLon, SicdObject


def sicd_polygon_wkt(points: Sequence[Union[LatLon, ImageCorner]]) -> str:
  if len(points) < 3:
    raise ValueError(f"Need at least 3 corners for a polygon, got {len('points')}")

  vertices = [f"{p['Lon']} {p['Lat']}" for p in points]

  if vertices[0] != vertices[-1]:
    vertices.append(vertices[0])

  return f"POLYGON(({', '.join(vertices)}))"


def parse_sicd_info(gdal_info: dict, sicd_obj: SicdObject):

  sicd = sicd_obj["metadata"]

  tifftag = tiff_metadata(gdal_info, "TIFFTAG_IMAGEDESCRIPTION") or {}
  tifftag = tifftag.get("collect", {}).get("image", {})

  collection_info = sicd["CollectionInfo"]
  geo_data = sicd["GeoData"]
  timeline = sicd["Timeline"]
  scpcoa = sicd["SCPCOA"]

  sensor_name = collection_info["CollectorName"]
  classification = collection_info["Classification"]
  interpretation_rating = collection_info.get("Parameters", {}).get("PREDICTED_RNIIRS")

  image_corners = geo_data["ImageCorners"]
  footprint = sicd_polygon_wkt(image_corners)

  datetime_collected = dt.fromisoformat(timeline["CollectStart"])
  look_angle = 90.0 - scpcoa["IncidenceAng"]
  azimuth_angle = scpcoa["AzimAng"]

  plane = sicd["RadarCollection"].get("Area", {}).get("Plane", {})

  gsd_row = plane.get("XDir", {}).get("LineSpacing") or tifftag.get(
    "ground_range_resolution"
  )

  gsd_col = plane.get("YDir", {}).get("SampleSpacing") or tifftag.get(
    "ground_azimuth_resolution"
  )

  return {
    "classification": classification,
    "datetime_collected": datetime_collected,
    "sensor_name": sensor_name,
    "footprint": footprint,
    "look_angle": look_angle,
    "azimuth_angle": azimuth_angle,
    "ground_sample_distance_row": gsd_row,
    "ground_sample_distance_col": gsd_col,
    "interpretation_rating": interpretation_rating,
  }
