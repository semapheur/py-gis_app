import json
from pathlib import Path

from src.bootstrap import load_env
from src.gdal_utils import gdalinfo

if __name__ == "__main__":
  load_env()

  tif = Path(
    r"C:\Users\danfy\Documents\Projects\py-gis_app\data\BJ3A_NYC_50cm_4bandbundle\BJ3A1_PAN1_20220615155359_L1_1015E3_ST_203_browser.tif"
  )

  test = gdalinfo(tif)
  with open("data/test.json", "w") as f:
    json.dump(test, f)
