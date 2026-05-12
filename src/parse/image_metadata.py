import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional

from src.gdal_utils import gdalinfo
from src.xml_utils import xml_to_dict


def parse_isd_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()

  if root.tag != "isd":
    raise ValueError("Invalid ISD XML")

  return {root.tag: xml_to_dict(root)}


def parse_b3j_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()
  return {"b3j": xml_to_dict(root)}


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
