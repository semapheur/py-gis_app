import re
from pathlib import Path
from typing import Optional, TypedDict, Union, cast

from src.gdal_utils import Band, gdalinfo
from src.parse.bj3_metadata import parse_bj3_xml
from src.parse.isd_metadata import parse_isd_xml


class BandStatistics(TypedDict):
  data_type: str
  color_interpretation: str
  min: Union[int, float]
  max: Union[int, float]
  mean: float
  stddev: float


def get_band_statistics(gdal_info: dict) -> list[BandStatistics]:
  bands = cast(Optional[list[Band]], gdal_info.get("bands"))
  if not isinstance(bands, list):
    raise ValueError("'bands' field missing or invalid in gdalinfo")

  result: list[BandStatistics] = []
  for band in bands:
    band_metadata = band.get("metadata", {}).get("", {})

    try:
      stats_min = band_metadata["STATISTICS_MINIMUM"]
      stats_max = band_metadata["STATISTICS_MAXIMUM"]
      stats_mean = band_metadata["STATISTICS_MEAN"]
      stats_stddev = band_metadata["STATISTICS_STDDEV"]
    except KeyError as e:
      raise ValueError(f"Missing expected statistics field: {e}") from e

    data_type = band["type"].lower()
    caster = float if "float" in data_type else int

    result.append(
      BandStatistics(
        data_type=data_type,
        color_interpretation=band["colorInterpretation"],
        min=caster(stats_min),
        max=caster(stats_max),
        mean=float(stats_mean),
        stddev=float(stats_stddev),
      )
    )

  return result


def parse_xml_metadata(tif_path: Path) -> Optional[dict]:
  if tif_path.name.lower().startswith("bj3"):
    xml_path = tif_path.with_suffix(".xml")
    if not xml_path.exists():
      return None

    return parse_bj3_xml(xml_path)

  aux_suffixes = {".aux", ".xml"}
  for f in tif_path.parent.glob("*.XML"):
    if aux_suffixes.issubset(f.suffixes):
      continue

    if not re.search(r"R\d+C\d+", f.name):
      return parse_isd_xml(f)

  return None


def parse_image_metadata(image_path: Path) -> dict:
  result = gdalinfo(image_path, stats="exact")

  driver = result["driverShortName"]

  if driver != "GTiff":
    return result

  xml_metadata = parse_xml_metadata(image_path)
  if xml_metadata is not None:
    result.update(xml_metadata)

  return result
