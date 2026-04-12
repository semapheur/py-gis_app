import json
from pathlib import Path
from typing import Literal, TypedDict

from src.bootstrap import get_settings
from src.spatialite import ColumnType, Field, Model, SqliteDatabase, hash_field

app_settings = get_settings()


class NoiseParameters(TypedDict):
  type: Literal["ABSOLUTE", "RELATIVE"]
  poly: list[list[float]]


polygon = Field(
  list[list[float]],
  ColumnType.TEXT,
  to_sql=lambda x: json.dumps(x),
  from_sql=lambda x: json.loads(x),
)


class RadiometricParamsTable(Model):
  _table_name = "radiometric_params"
  id = hash_field(True)
  noise = polygon
  sigma0 = polygon
  beta0 = polygon
  gamma0 = polygon


def get_radiometric_parameters(
  hash_id: bytes, factors: tuple[Literal["noise", "sigma0", "beta0", "gamma0"], ...]
):
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    rows = db.select_records(
      RadiometricParamsTable,
      columns=factors,
      where="id = :id",
      params={"id": hash_id},
      to_json=True,
    )
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
