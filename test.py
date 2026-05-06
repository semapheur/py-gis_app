import json
from pathlib import Path

from src.bootstrap import load_env
from src.gdal_utils import gdalinfo
from src.index.metadata import find_isd_xml

if __name__ == "__main__":
  load_env()

  tif = Path(
    r"C:\Users\danfy\Documents\Projects\py-gis_app\data\CAPELLA_C13_SP_SLC_HH_20241122024652_20241122024723.TIF"
  )

  test = gdalinfo(tif)
  with open("data/test.json", "w") as f:
    json.dump(test, f)
