import json
from pathlib import Path

from src.bootstrap import load_env
from src.gdal_utils import gdalinfo
from src.parse.iceye_metadata import parse_iceye_xml

if __name__ == "__main__":
  load_env()

  tif = Path(
    r"C:\Users\danfy\Documents\Projects\py-gis_app\data\056965205010_01_P001_PAN\17APR18154116-P2AS_R1C1-056965205010_01_P001.TIF"
  )

  xml_path = Path(
    r"C:\Users\danfy\Documents\Projects\py-gis_app\data\2631302_2024-12-04T17_15_25Z\2631302\ICEYE_X8_GRD_SM_2631302_20230903T192621.xml"
  )

  test = parse_iceye_xml(xml_path)

  # test = gdalinfo(tif)
  # metadata = info["metadata"][""]["TIFFTAG_IMAGEDESCRIPTION"]
  # test = json.loads(metadata)

  with open("data/test.json", "w") as f:
    json.dump(test, f)
