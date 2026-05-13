import xml.etree.ElementTree as ET
from datetime import datetime as dt
from pathlib import Path

from src.xml_utils import xml_to_dict


def parse_isd_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()

  if root.tag != "isd":
    raise ValueError(f"Invalid ISD XML: {xml_path}")

  return {root.tag: xml_to_dict(root)}


def find_tile_for_file(isd: dict, stem: str) -> dict:
  tiles = isd["TIL"]["TILE"]

  for tile in tiles:
    if Path(tile["FILENAME"]).stem == stem:
      return tile
  return {}


def isd_polygon_wkt(tile: dict) -> str:
  points = (
    f"{tile['ULLON']} {tile['ULLAT']}",
    f"{tile['URLON']} {tile['URLAT']}",
    f"{tile['LRLON']} {tile['LRLAT']}",
    f"{tile['LLLON']} {tile['LLLAT']}",
    f"{tile['ULLON']} {tile['ULLAT']}",
  )
  return f"POLYGON(({', '.join(points)}))"


def get_isd_info(file_path: Path, isd: dict) -> dict:
  image_info = isd["IMD"]["IMAGE"]
  tile_info = find_tile_for_file(isd, file_path.stem)

  datetime_collected = dt.fromisoformat(image_info.get("FIRSTLINETIME"))
  footprint = isd_polygon_wkt(tile_info)

  return {
    "classification": "UNCLASSIFIED",
    "datetime_collected": datetime_collected,
    "sensor_name": image_info["SATID"],
    "footprint": footprint,
    "look_angle": image_info["MEANOFFNADIRVIEWANGLE"],
    "azimuth_angle": image_info["MEANSATAZ"],
    "ground_sample_distance_row": image_info["MEANCOLLECTEDROWGSD"],
    "ground_sample_distance_col": image_info["MEANCOLLECTEDCOLGSD"],
    "interpretation_rating": image_info["PNIIRS"],
  }
