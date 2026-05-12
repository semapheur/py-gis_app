import xml.etree.ElementTree as ET
from pathlib import Path

from src.xml_utils import _float, _int


def find_tile_for_file(isd: dict, stem: str) -> dict:
  for tile in isd.get("tiles", []):
    if Path(tile.get("filename", "")).stem == stem:
      return tile
  return {}


def isd_polygon_wkt(tile: dict) -> str:
  points = (
    f"{tile['ullon']} {tile['ullat']}",
    f"{tile['urlon']} {tile['urlat']}",
    f"{tile['lrlon']} {tile['lrlat']}",
    f"{tile['lllon']} {tile['lllat']}",
    f"{tile['ullon']} {tile['ullat']}",
  )
  return f"POLYGON(({', '.join(points)}))"


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
    band_info = {
      child.tag.lower(): {subchild.tag.lower(): subchild.text for subchild in child}
      for child in imd
      if child.tag.startswith("BAND_")
    }
  else:
    band_element = imd.find(f"BAND_{band_id}") if band_id else None
    band_info = (
      {
        f"band_{band_id.lower()}": {
          child.tag.lower(): child.text for child in band_element
        }
      }
      if band_element is not None
      else {}
    )

  tile_info = []
  for tile in til.findall("TILE"):
    tile_info.append({child.tag.lower(): child.text for child in tile})

  image_info = {
    "satellite_id": image.findtext("SATID"),
    "acquisition_time": image.findtext("FIRSTLINETIME"),
    "scan_direction": imd.findtext("SCANDIRECTION"),
    "num_rows": _int(imd, "NUMROWS"),
    "num_columns": _int(imd, "NUMCOLUMNS"),
    "mean_gsd": _float(image, "MEANCOLLECTEDGSD"),
    "min_gsd_row": _float(image, "MINCOLLECTEDROWGSD"),
    "max_gsd_row": _float(image, "MAXCOLLECTEDROWGSD"),
    "mean_gsd_row": _float(image, "MEANCOLLECTEDROWGSD"),
    "min_gsd_col": _float(image, "MINCOLLECTEDCOLGSD"),
    "max_gsd_col": _float(image, "MAXCOLLECTEDCOLGSD"),
    "mean_gsd_col": _float(image, "MEANCOLLECTEDCOLGSD"),
    "min_sun_elevation": _float(image, "MINSUNEL"),
    "max_sun_elevation": _float(image, "MAXSUNEL"),
    "mean_sun_elevation": _float(image, "MEANSUNEL"),
    "min_sun_azimuth": _float(image, "MINSUNAZ"),
    "max_sun_azimuth": _float(image, "MAXSUNAZ"),
    "mean_sun_azimuth": _float(image, "MEANSUNAZ"),
    "min_sat_elevation": _float(image, "MINSATEL"),
    "max_sat_elevation": _float(image, "MAXSATEL"),
    "mean_sat_elevation": _float(image, "MEANSATEL"),
    "min_sat_azimuth": _float(image, "MINSATAZ"),
    "max_sat_azimuth": _float(image, "MAXSATAZ"),
    "mean_sat_azimuth": _float(image, "MEANSATAZ"),
    "min_off_nadir": _float(image, "MINOFFNADIRVIEWANGLE"),
    "max_off_nadir": _float(image, "MAXOFFNADIRVIEWANGLE"),
    "mean_off_nadir": _float(image, "MEANOFFNADIRVIEWANGLE"),
    "min_intrack_angle": _float(image, "MININTRACKVIEWANGLE"),
    "max_intrack_angle": _float(image, "MAXINTRACKVIEWANGLE"),
    "mean_intrack_angle": _float(image, "MEANINTRACKVIEWANGLE"),
    "min_crosstrack_angle": _float(image, "MINCROSSTRACKVIEWANGLE"),
    "max_crosstrack_angle": _float(image, "MAXCROSSTRACKVIEWANGLE"),
    "mean_crosstrack_angle": _float(image, "MEANCROSSTRACKVIEWANGLE"),
    "pniirs": _float(image, "PNIIRS"),
    "cloud_cover": _float(image, "CLOUDCOVER"),
  }

  return {
    "isd": {
      "imd": {
        "product_level": imd.findtext("PRODUCTLEVEL"),
        "product_type": imd.findtext("PRODUCTTYPE"),
        "radiometric_level": imd.findtext("RADIOMETRICLEVEL"),
        "bits_per_pixel": _int(imd, "BITSPERPIXEL"),
        "image": image_info,
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
