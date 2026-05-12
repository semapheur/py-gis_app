import re
from pathlib import Path
from typing import Optional, TypedDict, cast
from uuid import UUID

from src.gdal_utils import Band, gdalinfo
from src.index.radiometric import make_radiometric_row
from src.parse.bj3_metadata import parse_b3j_xml
from src.parse.isd_metadata import parse_isd_xml


class BandStatistics(TypedDict):
  data_type: str
  color_interpretation: str
  min: int
  max: int
  mean: float
  std: float


def get_band_statistics(gdal_info: dict) -> list[BandStatistics]:
  bands = cast(Optional[list[Band]], gdal_info.get("bands"))
  if bands is None:
    raise ValueError("'bands' field missing from gdalinfo")

  band_statistics = [
    BandStatistics(
      data_type=band["type"],
      color_interpretation=band["colorInterpretation"],
      min=band["min"],
      max=band["max"],
      mean=band["mean"],
      std=band["stdDev"],
    )
    for band in bands
  ]

  return band_statistics


def parse_xml_metadata(tif_path: Path) -> Optional[dict]:
  if tif_path.name.lower().startswith("b3j"):
    xml_path = tif_path.with_suffix(".xml")
    if not xml_path.exists():
      return None

    return parse_b3j_xml(xml_path)

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


def parse_image_info(
  gdal_info: dict,
  hash: bytes,
  catalog_id: UUID,
  file_path: Path,
  relative_directory: Path,
) -> tuple[ImageIndexTable, Union[RadiometricParamsTable, None]]:

  band_statistics = get_band_statistics(gdal_info)
  sensor_type, image_type = detect_image_type(band_statistics, gdal_info)

  data = {
    "id": hash,
    "catalog": catalog_id,
    "relative_path": relative_directory,
    "filename": file_path.stem,
    "filetype": file_path.suffix,
    "sensor_type": sensor_type,
    "image_type": image_type,
    "band_statistics": band_statistics,
  }

  isd = gdal_info.get("isd")
  if isd is not None:
    isd_data = get_isd_info(file_path, isd)
    data |= isd_data
    index_row = make_index_row(data)
    return index_row, None

  sicd_obj = tiff_metadata(gdal_info, "SICD_METADATA")
  if sicd_obj is not None:
    sicd_data = parse_sicd_metadata(gdal_info, cast(SicdObject, sicd_obj))
    data |= sicd_data
    index_row = make_index_row(data)

    if image_type != ImageryType.SLC:
      return index_row, None

    radiometric_row = make_radiometric_row(sicd_obj["metadata"], hash)
    return index_row, radiometric_row
