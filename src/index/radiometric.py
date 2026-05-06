import json
from pathlib import Path
from typing import Literal, TypeAlias, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import Query
from src.sqlite.table import ColumnType, Field, Table, hash_field, json_field

app_settings = get_settings()

RadiometricFactors: TypeAlias = Literal["noise", "sigma0", "beta0", "gamma0"]


class NoiseParameters(TypedDict):
  type: Literal["ABSOLUTE", "RELATIVE"]
  poly: list[list[float]]


polygon = json_field(list[list[float]])


class RadiometricParamsTable(Table):
  _table_name = "radiometric_params"
  id = hash_field(True)
  noise = polygon
  sigma0 = polygon
  beta0 = polygon
  gamma0 = polygon


def create_radiometric_table():
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    db.create_table(RadiometricParamsTable)


def get_radiometric_parameters(hash_id: bytes, factors: tuple[RadiometricFactors, ...]):
  query = (
    Query()
    .select(*factors)
    .from_(RadiometricParamsTable._table_name)
    .where("id = ?", hash_id)
  )

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    rows = db.select_records(RadiometricParamsTable, query, True)
    return rows[0]


def generate_intensity_vrt(image_path: Path, vrt_path: Path, gdal_info: dict):
  width, height = gdal_info["size"]
  geo_info = gdal_info.get("gcps")
  if geo_info is None:
    raise ValueError(f"'gcps' not in metadata for {str(image_path)}")

  srs_wkt = geo_info.get("coordinateSystem", {}).get("wkt", "EPSG:4326")
  gcps = geo_info.get("gcpList", [])

  vrt_lines = [
    f'<VRTDataset rasterXSize="{width}" rasterYSize="{height}">',
    f"<SRS>{srs_wkt}</SRS>",
    "<GCPList>",
  ]

  for g in gcps:
    vrt_lines.append(
      f'<GCP Id="{g["id"]}" '
      f'Pixel="{g["pixel"]}" '
      f'Line="{g["line"]}" '
      f'X="{g["x"]}" '
      f'Y="{g["y"]}" '
      f'Z="{g.get("z", 0)}"/>'
    )

  vrt_lines.extend(
    [
      "</GCPList>",
      (
        "<VRTRasterBand dataType='Float32' band='1'>"
        "<PixelFunctionType>complex_magnitude_squared</PixelFunctionType>"
        "<SourceTransferType>Float32</SourceTransferType>"
        "<SimpleSource>"
        f"<SourceFilename>{str(image_path)}</SourceFilename>"
        "<SourceBand>1</SourceBand>"
        "</SimpleSource>"
        "</VRTRasterBand>"
        "</VRTDataset>"
      ),
    ]
  )

  with open(vrt_path, "w", encoding="utf-8") as f:
    f.write("".join(vrt_lines))
