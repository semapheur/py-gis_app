import json
import xml.etree.ElementTree as ET
from pathlib import Path

from src.bootstrap import load_env
from src.gdal_utils import gdalinfo
from src.xml_utils import xml_to_dict

if __name__ == "__main__":
  load_env()

  tif = Path(
    r"C:\Users\danfy\Documents\Projects\py-gis_app\data\056965205010_01_P001_PAN\17APR18154116-P2AS-056965205010_01_P001.XML"
  )

  # test = gdalinfo(tif, stats="exact")
  tree = ET.parse(tif)
  root = tree.getroot()
  test = xml_to_dict(root)
  with open("data/test.json", "w") as f:
    json.dump(test, f)
