import json
import math
from datetime import datetime as dt
from typing import Optional

from src.geo_utils import rpc_polynomial
from src.math_utils import dot


def rpc_pixel_to_latlon(
  line: float, sample: float, rpc: dict, height: Optional[float] = None
) -> tuple[float, float]:
  lat_off = float(rpc["LAT_OFF"])
  lat_scale = float(rpc["LAT_SCALE"])
  lon_off = float(rpc["LONG_OFF"])
  lon_scale = float(rpc["LONG_SCALE"])
  line_off = float(rpc["LINE_OFF"])
  line_scale = float(rpc["LINE_SCALE"])
  samp_off = float(rpc["SAMP_OFF"])
  samp_scale = float(rpc["SAMP_SCALE"])
  height_off = float(rpc["HEIGHT_OFF"])
  height_scale = float(rpc["HEIGHT_SCALE"])

  line_num = list(map(float, rpc["LINE_NUM_COEFF"].split()))
  line_den = list(map(float, rpc["LINE_DEN_COEFF"].split()))
  samp_num = list(map(float, rpc["SAMP_NUM_COEFF"].split()))
  samp_den = list(map(float, rpc["SAMP_DEN_COEFF"].split()))

  L = (line - line_off) / line_scale
  S = (sample - samp_off) / samp_scale
  H = ((height if height is not None else height_off) - height_off) / height_scale

  lat = lat_off + lat_scale * (
    rpc_polynomial(line_num, L, S, H) / rpc_polynomial(line_den, L, S, H)
  )
  lon = lon_off + lon_scale * (
    rpc_polynomial(samp_num, L, S, H) / rpc_polynomial(samp_den, L, S, H)
  )
  return lon, lat


def capella_polygon_wkt(gdal_info: dict):
  rpc = gdal_info["RPC"]
  width = gdal_info["size"][0]
  height = gdal_info["size"][1]

  ring = [
    rpc_pixel_to_latlon(0, 0, rpc),
    rpc_pixel_to_latlon(0, width, rpc),
    rpc_pixel_to_latlon(height, width, rpc),
    rpc_pixel_to_latlon(height, 0, rpc),
  ]
  ring.append(ring[0])

  polygon_coords = ", ".join(f"{lon} {lat}" for lon, lat in ring)
  return f"POLYGON(({polygon_coords}))"


def capella_sensor_azimuth(capella_data: dict) -> float:
  image_geometry = capella_data["collect"]["image"]["image_geometry"]

  arp = image_geometry["center_of_aperture"]["antenna_reference_point"]
  scp = image_geometry["scene_reference_point_ecef"]

  los = [arp[i] - scp[i] for i in range(3)]

  x, y, z = scp
  lon_r = math.atan2(y, x)
  lat_r = math.atan2(z, math.sqrt(x**2 + y**2))

  e_east = [-math.sin(lon_r), math.cos(lon_r), 0]
  e_north = [
    -math.sin(lat_r) * math.cos(lon_r),
    -math.sin(lat_r) * math.sin(lon_r),
    math.cos(lat_r),
  ]

  azimuth = math.degrees(math.atan2(dot(los, e_east), dot(los, e_north))) % 360
  return azimuth


def get_capella_info(gdal_info: dict):
  capella_data = json.loads(gdal_info["metadata"][""]["TIFFTAG_IMAGEDESCRIPTION"])

  datetime_collected = dt.fromisoformat(capella_data["collect"]["stop_timestamp"])

  footprint = capella_polygon_wkt(capella_data)

  center_pixel = capella_data["collect"]["image"]["center_pixel"]

  return {
    "classification": "UNCLASSIFIED",
    "datetime_collected": datetime_collected,
    "sensor_name": capella_data["collect"]["platform"],
    "footprint": footprint,
    "look_angle": center_pixel["look_angle"],
    "azimuth_angle": capella_sensor_azimuth(capella_data),
    "ground_sample_distance_row": center_pixel["ground_azimuth_resolution"],
    "ground_sample_distance_col": center_pixel["ground_range_resolution"],
    "interpretation_rating": None,
  }
