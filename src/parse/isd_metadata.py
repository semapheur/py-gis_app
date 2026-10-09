import xml.etree.ElementTree as ET
from datetime import datetime as dt
from pathlib import Path
from typing import Optional

from src.index.rpc import RpcTable
from src.xml_utils import xml_to_dict

_RPC_SCALAR_FIELDS = {
  "line_offset": "LINEOFFSET",
  "line_scale": "LINESCALE",
  "sample_offset": "SAMPOFFSET",
  "sample_scale": "SAMPSCALE",
  "latitude_offset": "LATOFFSET",
  "latitude_scale": "LATSCALE",
  "longitude_offset": "LONGOFFSET",
  "longitude_scale": "LONGSCALE",
  "height_offset": "HEIGHTOFFSET",
  "height_scale": "HEIGHTSCALE",
}

_RPC_COEFFICIENT_FIELDS = {
  "line_numerator_coefficients": "LINENUM",
  "line_denominator_coefficients": "LINEDEN",
  "sample_numerator_coefficients": "SAMPNUM",
  "sample_denominator_coefficients": "SAMPDEN",
}


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


def get_isd_rpc(isd: dict, image_hash: bytes) -> RpcTable:
  def _float(key: str) -> Optional[float]:
    value = rpc.get(key)
    return None if value is None else float(value)

  def _parse_coefficients(prefix: str) -> list[float]:
    values = list(map(float, rpc[f"{prefix}COEFList"][f"{prefix}COEF"].split()))
    if len(values) != 20:
      raise ValueError(f"{prefix}COEF has {len(values)} values, expected 20")

    return values

  try:
    rpc = isd["RPB"]["IMAGE"]
    params: dict = {"id": image_hash}

    for field, key in _RPC_SCALAR_FIELDS.items():
      params[field] = float(rpc[key])

    for field, prefix in _RPC_COEFFICIENT_FIELDS.items():
      params[field] = _parse_coefficients(prefix)

  except KeyError as e:
    raise ValueError(f"ISD RPB is missing required key {e}") from e

  params["err_bias"] = _float("ERRBIAS")
  params["err_random"] = _float("ERRRAND")

  return RpcTable().from_dict(params)


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
