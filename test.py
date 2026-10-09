import json
from pathlib import Path

from src.bootstrap import get_settings, load_env
from src.gdal_utils import gdalinfo

if __name__ == "__main__":
  load_env()
  app_settings = get_settings()

  ntf_path = Path(
    "data/056965205010_01_P001_PAN/17APR18154116-P2AS_R1C1-056965205010_01_P001.TIF"
  )
  test = gdalinfo(ntf_path)
  with open("data/test.json", "w") as file:
    json.dump(test, file, indent=2)
