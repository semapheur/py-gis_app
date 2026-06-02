import xml.etree.ElementTree as ET
from datetime import datetime as dt
from pathlib import Path

from src.xml_utils import xml_to_dict


def parse_iceye_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()
  return {"iceye": xml_to_dict(root)}


def iceye_polygon_wkt(iceye_data: dict):

  corner_fields = (
    "coord_first_near",
    "coord_first_far",
    "coord_last_near",
    "coord_last_far",
  )

  metadata = iceye_data["Metadata"]
  points = []
  for key in corner_fields:
    parts = metadata[key].split()
    lon = parts[3]
    lat = parts[2]
    points.append(f"{lon} {lat}")

  points.append(points[0])
  return f"POLYGON(({', '.join(points)}))"


def get_iceye_info(iceye_data: dict):

  datetime_collected = dt.fromisoformat(iceye_data["acquisition_end_utc"])
  footprint = iceye_polygon_wkt(iceye_data)

  heading = iceye_data["heading"]
  look_side = iceye_data["look_side"]
  offset = -90 if look_side == "left" else 90
  azimuth_angle = (heading + offset) % 360

  return {
    "classification": "UNCLASSIFIED",
    "datetime_collected": datetime_collected,
    "sensor_name": iceye_data["satellite_name"],
    "footprint": footprint,
    "look_angle": iceye_data["satellite_look_angle"],
    "azimuth_angle": azimuth_angle,
    "ground_sample_distance_row": iceye_data["azimuth_resolution"],
    "ground_sample_distance_col": iceye_data["range_resolution_center"],
    "interpretation_rating": None,
  }
