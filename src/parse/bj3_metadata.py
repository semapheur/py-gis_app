import xml.etree.ElementTree as ET
from datetime import datetime as dt
from pathlib import Path
from typing import Literal, TypeAlias

from src.xml_utils import xml_to_dict

LocationType: TypeAlias = Literal[
  "TopLeft", "TopRight", "Center", "BottomLeft", "BottomRight"
]


def parse_bj3_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()
  return {"bj3": xml_to_dict(root)}


def find_geometric_data(bj3: dict, location: LocationType = "Center"):
  geodata = bj3["Geometric_Data"]["Use_Area"]["Located_Geometric_Values"]

  for point_data in geodata:
    if point_data["LOCATION_TYPE"] == location:
      return point_data

  return None


def bj3_polygon_wkt(bj3: dict) -> str:
  vertices = bj3["Image_Extent"]["Vertex"]

  points = [f"{v['LON']} {v['LAT']}" for v in vertices]
  points.append(points[0])

  return f"POLYGON(({', '.join(points)}))"


def get_bj3_info(bj3: dict):
  datetime_collected = dt.fromisoformat(bj3["Product_Information"]["IMAGING_TIME_UTC"])
  footprint = bj3_polygon_wkt(bj3)

  center_geodata = find_geometric_data(bj3, "Center")
  if center_geodata is None:
    raise ValueError("bj3 metadata is missing Geometric_Data field")

  acquisition_angles = center_geodata["Acquisition_Angles"]

  return {
    "classification": "UNCLASSIFIED",
    "datetime_collected": datetime_collected,
    "sensor_name": bj3["General_Information"]["IMAGING_SATELLITE"],
    "footprint": footprint,
    "look_angle": acquisition_angles["VIEW_ANGLE"],
    "azimuth_angle": acquisition_angles["SATELLITE_AZIMUTH"],
    "ground_sample_distance_row": acquisition_angles["GSD_ACROSS_TRACK"],
    "ground_sample_distance_col": acquisition_angles["GSD_ALONG_TRACK"],
    "interpretation_rating": None,
  }
