import json
from pathlib import Path
from pprint import pprint

from src.gdal_utils import GdalTranslateOptions, band_ranges, gdal_translate, gdalinfo
from src.imagery_index import ImageIndexTable, index_images
from src.spatialite import SpatialDatabase

if __name__ == "__main__":
  # image_folder = Path("data")
  # index_images(image_folder)

  image_path = Path("data/CAPELLA_C13_SP_SLC_HH_20241122024652_20241122024723.tif")
  thumbnail_path = Path("CAPELLA_C13_SP_SLC_HH_20241122024652_20241122024723.png")

  ranges = band_ranges(image_path, 1000)
  print(ranges)

  options = GdalTranslateOptions(outsize=(600, 598), scale_x=ranges)
  gdal_translate(image_path, thumbnail_path, "PNG", options)

  # test = gdalinfo(image_path)
  # tifftag = test.get("metadata", {}).get("", {}).get("SICD_METADATA")
  # tifftag = json.loads(tifftag)

# with open("sicd.json", "w") as f:
#  json.dump(tifftag, f, indent=2)

# db_path = Path("db/index.db")
