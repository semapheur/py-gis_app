import json
from pathlib import Path

from src.bootstrap import get_settings, load_env
from src.gdal_utils import gdalinfo

if __name__ == "__main__":
  load_env()
  app_settings = get_settings()

  ntf_path = Path(
    "data/2019-10-05T100157_RE4/basic_analytic_nitf/2019-10-05T100157_RE4_1B_band1.ntf"
  )
  test = gdalinfo(ntf_path)
  with open("data/ntf_metadata.json", "w") as file:
    json.dump(test, file, indent=2)
