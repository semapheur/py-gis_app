import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


def _float(element: ET.Element, tag: str) -> float:
  value = element.findtext(tag)
  if value is None:
    raise ValueError(f"Missing required tag: {tag}")

  return float(value)


def _int(element: ET.Element, tag: str) -> int:
  value = element.findtext(tag)
  if value is None:
    raise ValueError(f"Missing required tag: {tag}")

  return int(value)


def find_isd_xml(tif_path: Path) -> Optional[Path]:

  for f in tif_path.parent.glob("*.XML"):
    if f.suffixes == [".aux", ".xml"]:
      continue

    if not re.search(r"R\d+C\d+", f.name):
      return f

  return None


def parse_isd_xml(xml_path: Path) -> dict:
  tree = ET.parse(xml_path)
  root = tree.getroot()

  if root.tag != "isd":
    raise ValueError("Invalid ISD XML")

  imd = root.find("IMD")
  if imd is None:
    raise ValueError("ISD XML missing IMD tag")

  image = imd.find("IMAGE")
  if image is None:
    raise ValueError("ISD XML missing IMD/IMAGE tag")

  proj = imd.find("MAP_PROJECTED_PRODUCT")

  til = root.find("TIL")
  if til is None:
    raise ValueError("ISD XML missing TIL tag")

  rpb = root.find("RPB/IMAGE")
  if rpb is None:
    raise ValueError("ISD XML missing RPB tag")

  band_id = imd.findtext("BANDID")
  if band_id is None:
    raise ValueError("ISD tag missing BANDID")

  if band_id == "Multi":
    bands = {
      child.tag.lower(): {subchild.tag.lower(): subchild.text for subchild in child}
      for child in imd
      if child.tag.startswith("BAND_")
    }
  else:
    band_element = imd.find(f"BAND_{band_id}") if band_id else None
    bands = (
      {
        f"band_{band_id.lower()}": {
          child.tag.lower(): child.text for child in band_element
        }
      }
      if band_element is not None
      else {}
    )

  tile_metadata = []
  for tile in til.findall("TILE"):
    tile_metadata.append({child.tag.lower(): child.text for child in tile})

  return {
    "isd": {
      "image": {
        "satellite": image.findtext("SATID"),
        "acquisition_time": image.findtext("FIRSTLINETIME"),
        "scan_direction": imd.findtext("IMAGEDESCRIPTOR"),
        "product_level": imd.findtext("PRODUCTLEVEL"),
        "product_type": imd.findtext("PRODUCTTYPE"),
        "radiometric_level": imd.findtext("RADIOMETRICLEVEL"),
        "bits_per_pixel": _int(imd, "BITSPERPIXEL"),
        "num_rows": _int(imd, "NUMROWS"),
        "num_columns": _int(imd, "NUMCOLUMNS"),
        "cloud_cover": _float(image, "CLOUDCOVER"),
        "mean_gsd_m": _float(image, "MEANCOLLECTEDGSD"),
        "min_gsd_m": _float(image, "MINCOLLECTEDROWGSD"),
        "max_gsd_m": _float(image, "MAXCOLLECTEDROWGSD"),
        "mean_sun_elevation": _float(image, "MEANSUNEL"),
        "mean_sun_azimuth": _float(image, "MEANSUNAZ"),
        "mean_sat_elevation": _float(image, "MEANSATEL"),
        "mean_sat_azimuth": _float(image, "MEANSATAZ"),
        "mean_off_nadir": _float(image, "MEANOFFNADIRVIEWANGLE"),
        "mean_intrack_angle": _float(image, "MEANINTRACKVIEWANGLE"),
        "mean_crosstrack_angle": _float(image, "MEANCROSSTRACKVIEWANGLE"),
        "pniirs": _float(image, "PNIIRS"),
      },
      "bands": bands,
      "projection": {
        "datum": proj.findtext("DATUMNAME"),
        "projection": proj.findtext("MAPPROJNAME"),
        "utm_zone": proj.findtext("MAPZONE"),
        "hemisphere": proj.findtext("MAPHEMI"),
        "pixel_spacing_m": _float(proj, "COLSPACING"),
        "product_gsd_m": _float(proj, "PRODUCTGSD"),
        "dem_correction": proj.findtext("DEMCORRECTION"),
        "terrain_hae": _float(proj, "TERRAINHAE"),
      }
      if proj is not None
      else None,
      "tiles": tile_metadata,
      "rpc": {
        "err_bias": _float(rpb, "ERRBIAS"),
        "err_rand": _float(rpb, "ERRRAND"),
        "line_offset": _int(rpb, "LINEOFFSET"),
        "samp_offset": _int(rpb, "SAMPOFFSET"),
        "lat_offset": _float(rpb, "LATOFFSET"),
        "long_offset": _float(rpb, "LONGOFFSET"),
        "height_offset": _int(rpb, "HEIGHTOFFSET"),
      }
      if rpb is not None
      else None,
    }
  }
