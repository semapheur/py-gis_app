import json
from pathlib import Path
from pprint import pprint

from src.gdal_utils import (
  CogOptions,
  GdalTranslateOptions,
  GdalWarpOptions,
  gdal_translate,
  gdalinfo,
  gdalwarp,
  geotiff_to_thumbnail,
)
from src.index.images import ImageIndexTable, index_images
from src.spatialite import SpatialDatabase

if __name__ == "__main__":
  image_folder = Path("data")
  index_images(image_folder, "main")

  # file_stem = "CAPELLA_C13_SP_SLC_HH_20241122024652_20241122024723"
  # image_path = Path(f"data/{file_stem}.tif")
  # thumbnail_path = Path("CAPELLA_C13_SP_SLC_HH_20241122024652_20241122024723.png")
  # cog_path = Path(f"static/cog/{file_stem}.cog.tif")
  # options = GdalWarpOptions(
  #  output_format="COG",
  #  creation_options=CloudOptimizedTiffOptions(bigtiff="YES", geotiff_version="1.1"),
  # )
  # gdalwarp(image_path, cog_path, options)

  # geotiff_to_thumbnail(image_path, thumbnail_path, (600, 598))
  # ranges = band_ranges(image_path, 1000)
  # options = GdalWarpOptions(output_format="PNG", outsize=(600, 598), tps=True)
  # gdalwarp(image_path, thumbnail_path, options)

  # test = gdalinfo(image_path)
  # tifftag = test.get("metadata", {}).get("", {}).get("SICD_METADATA")
  # tifftag = json.loads(tifftag)
#
# with open("sicd.json", "w") as f:
#  json.dump(tifftag, f, indent=2)

# db_path = Path("db/index.db")
