import json
from pathlib import Path

from src.bootstrap import load_env
from src.gdal_utils import gdalinfo

if __name__ == "__main__":
  load_env()

  test = gdalinfo(
    Path(
      r"C:\Users\danfy\Documents\Projects\py-gis_app\data\056965205010_01_P001_PAN\17APR18154116-P2AS_R1C1-056965205010_01_P001.TIF"
    )
  )

  with open("data/test.json", "w") as f:
    json.dump(test, f, indent=2)
