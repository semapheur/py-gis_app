import xml.etree.ElementTree as ET
from datetime import datetime as dt
from pathlib import Path
from typing import Literal, TypeAlias

from src.xml_utils import xml_to_dict

LocationType: TypeAlias = Literal[
  "TopLeft", "TopRight", "Center", "BottomLeft", "BottomRight"
]


def parse_b3j_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()
  return {"b3j": xml_to_dict(root)}


def find_geometric_data(b3j: dict, location: LocationType = "Center"):
  geodata = b3j["Geometric_Data"]["Use_Area"]

  for point_data in geodata:
    if point_data["LOCATION_TYPE"] == location:
      return point_data

  return None


def b3j_polygon_wkt(b3j: dict) -> str:
  vertices = b3j["Image_Extent"]["Vertex"]

  points = [f"{v['LON']} {v['LAT']}" for v in vertices]
  points += points[0]

  return f"POLYGON(({', '.join(points)}))"


def get_b3j_info(b3j: dict):
  datetime_collected = dt.fromisoformat(b3j["PRODUCT_INFORMATION"]["IMAGING_TIME_UTC"])
  footprint = b3j_polygon_wkt(b3j)

  center_geodata = find_geometric_data(b3j, "Center")
  if center_geodata is None:
    raise ValueError("b3j metadata is missing Geometric_Data field")

  return {
    "classification": "UNCLASSIFIED",
    "datetime_collected": datetime_collected,
    "sensor_name": b3j["General_Information"]["IMAGING_SATELLITE"],
    "footprint": footprint,
    "look_angle": center_geodata["VIEW_ANGLE"],
    "azimuth_angle": center_geodata["SATELLITE_AZIMUTH"],
    "ground_sample_distance_row": center_geodata["GSD_ACROSS_TRACK"],
    "ground_sample_distance_col": center_geodata["GSD_ALONG_TRACK"],
    "interpretation_rating": None,
  }
