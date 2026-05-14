import json
import warnings
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable, Literal, Optional, TypedDict, Union, cast
from uuid import UUID

from src.bootstrap import get_settings
from src.gdal_utils import (
  CogOptions,
  GdalTranslateOptions,
  GdalWarpOptions,
  gdal_translate,
  gdalwarp,
  parse_gdalinfo_json_field,
)
from src.hashing import hash_geotiff
from src.index.catalog import CatalogTable, get_catalog_edit_data, update_index_time
from src.index.radiometric import RadiometricParamsTable, make_radiometric_row
from src.models.areas import get_area_wkt
from src.parse.bj3_metadata import get_bj3_info
from src.parse.image_metadata import (
  BandStatistics,
  get_band_statistics,
  parse_image_metadata,
)
from src.parse.isd_metadata import get_isd_info
from src.parse.sicd_metadata import parse_sicd_info
from src.parse.sicd_model import SicdObject
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import OnConflict, Query
from src.sqlite.table import (
  ColumnType,
  Field,
  GeometryField,
  Table,
  datetime_field,
  enum_field,
  hash_field,
  json_field,
  path_field,
  uuid_field,
)

app_settings = get_settings()


class ImagerySensorType(Enum):
  EO = "eo"
  SAR = "sar"


class ImageryType(str, Enum):
  GRD = "grd"
  PAN = "pan"
  MS = "ms"
  SLC = "slc"


class ImageIndexTable(Table):
  _table_name = "images"
  id = hash_field(True)
  catalog = uuid_field(False, False)
  relative_path = path_field(False, False)
  filename = Field(str, nullable=False)
  filetype = Field(str, nullable=False)
  classification = Field(str)
  datetime_collected = datetime_field(False)
  sensor_name = Field(str)
  sensor_type = enum_field(ImagerySensorType, ColumnType.TEXT)
  image_type = enum_field(ImageryType, ColumnType.TEXT)
  footprint = GeometryField(str, geometry_type="POLYGON")
  look_angle = Field(float)
  azimuth_angle = Field(float)
  ground_sample_distance_row = Field(float)
  ground_sample_distance_col = Field(float)
  interpretation_rating = Field(float)
  band_statistics = json_field(list[BandStatistics], nullable=False)


def create_index_table():
  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    db.create_table(ImageIndexTable)


def detect_image_type(
  bands: list[BandStatistics], gdal_info: dict
) -> tuple[ImagerySensorType, ImageryType]:

  metadata = gdal_info.get("metadata", {}).get("", {})
  complex_bands = [band["data_type"].lower().startswith("c") for band in bands]
  if any(complex_bands):
    return (ImagerySensorType.SAR, ImageryType.SLC)

  if "SICD_METADATA" in metadata:
    return (ImagerySensorType.SAR, ImageryType.GRD)

  num_bands = len(bands)
  if num_bands == 1:
    return (ImagerySensorType.EO, ImageryType.PAN)

  return (ImagerySensorType.EO, ImageryType.MS)


def make_index_row(data: dict) -> ImageIndexTable:
  row = ImageIndexTable()
  for key, value in data.items():
    setattr(row, key, value)

  return row


def parse_image_info(
  gdal_info: dict,
  hash: bytes,
  catalog_id: UUID,
  file_path: Path,
  relative_directory: Path,
) -> tuple[ImageIndexTable, Union[RadiometricParamsTable, None]]:

  band_statistics = get_band_statistics(gdal_info)
  sensor_type, image_type = detect_image_type(band_statistics, gdal_info)

  data = {
    "id": hash,
    "catalog": catalog_id,
    "relative_path": relative_directory,
    "filename": file_path.stem,
    "filetype": file_path.suffix,
    "sensor_type": sensor_type,
    "image_type": image_type,
    "band_statistics": band_statistics,
  }

  isd = gdal_info.get("isd")
  if isd is not None:
    isd_data = get_isd_info(file_path, isd)
    data |= isd_data
    index_row = make_index_row(data)
    return index_row, None

  bj3 = gdal_info.get("bj3")
  if bj3 is not None:
    bj3_data = get_bj3_info(bj3)
    data |= bj3_data
    index_row = make_index_row(data)
    return index_row, None

  sicd_obj = parse_gdalinfo_json_field(gdal_info, "SICD_METADATA")
  if sicd_obj is not None:
    sicd_data = parse_sicd_info(gdal_info, cast(SicdObject, sicd_obj))
    data |= sicd_data
    index_row = make_index_row(data)

    if image_type != ImageryType.SLC:
      return index_row, None

    radiometric_row = make_radiometric_row(sicd_obj["metadata"], hash)
    return index_row, radiometric_row


def generate_cog(image_path: Path, cog_path: Path):
  if cog_path.exists():
    warnings.warn(f"COG already generated for {str(image_path)}")
    return

  options = GdalWarpOptions(
    output_format="COG",
    resampling="nearest",
    creation_options=CogOptions(
      bigtiff="YES",
      geotiff_version="1.1",
      compress="LZW",
      predictor="YES",
      num_threads="ALL_CPUS",
      resampling="NEAREST",
    ),
  )

  gdalwarp(
    image_path,
    cog_path,
    options,
  )
  return


def generate_thumbnail(
  image_path: Path,
  thumbnail_path: Path,
  gsd: tuple[float, float],
  image_size: tuple[int, int],
  thumbnail_minsize: tuple[int, int],
):
  image_width, image_height = image_size
  gsd_row, gsd_col = gsd
  max_gsd = max(gsd_row, gsd_col)

  width = int(image_width * (gsd_row / max_gsd))
  height = int(image_height * (gsd_col / max_gsd))
  aspect = width / height
  min_width, min_height = thumbnail_minsize

  thumbnail_width = min_width if aspect < 1 else int(min_height * aspect)
  thumbnail_height = min_height if aspect > 1 else int(min_width * aspect)

  options = GdalTranslateOptions(
    output_format="PNG",
    outsize=(thumbnail_width, thumbnail_height),
  )

  gdal_translate(
    input_path=image_path,
    output_path=thumbnail_path,
    options=options,
  )


class IndexAction(Enum):
  NOT_INDEXED = "not_indexed"
  REINDEX_PARENT = "reindex_parent"
  REINDEX_FILENAME = "reindex_filename"
  INDEXED = "indexed"
  DUPLICATE = "duplicate"


def check_image(image_path: Path, hash: bytes) -> tuple[IndexAction, Union[str, None]]:
  query = (
    Query()
    .select(
      "concat(c.path, '/', i.relative_path, '/', i.filename, '.', i.filetype) AS path"
    )
    .from_(f"{ImageIndexTable._table_name} i")
    .inner_join("catalog c", "c.id = i.catalog")
    .where("i.id = ?", hash)
  )

  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    result = db.select_records(ImageIndexTable, query)

  if not result:
    return (IndexAction.NOT_INDEXED, None)

  indexed_path = Path(result[0]["path"])

  if not indexed_path.exists():
    if indexed_path.stem != image_path.stem:
      return (IndexAction.REINDEX_FILENAME, indexed_path.stem)

    return (IndexAction.REINDEX_PARENT, None)

  if indexed_path == image_path.resolve():
    return (IndexAction.INDEXED, None)

  return (IndexAction.DUPLICATE, None)


def process_thumbnail(
  image_file: Path,
  image_info: dict,
  index_row: ImageIndexTable,
  action: IndexAction,
  old_stem: Optional[str],
  minsize: tuple[int, int],
):
  thumbnail_dir = app_settings.STATIC_DIR / "thumbnails"
  thumbnail_dir.mkdir(parents=True, exist_ok=True)

  thumbnail_path = thumbnail_dir / f"{image_file.stem}.png"
  make_thumbnail = not thumbnail_path.exists()

  if action == IndexAction.REINDEX_FILENAME and old_stem is not None:
    old_thumbnail = thumbnail_dir / f"{old_stem}.png"
    if old_thumbnail.exists():
      old_thumbnail.rename(thumbnail_path)
      make_thumbnail = False

  if make_thumbnail:
    image_size = image_info["size"]
    gsd = (
      getattr(index_row, "ground_sample_distance_row"),
      getattr(index_row, "ground_sample_distance_col"),
    )
    generate_thumbnail(image_file, thumbnail_path, gsd, image_size, minsize)


def process_cog(
  image_file: Path,
  action: IndexAction,
  old_stem: Optional[str],
):
  cog_dir = app_settings.STATIC_DIR / "cog"
  cog_dir.mkdir(parents=True, exist_ok=True)
  cog_path = cog_dir / f"{image_file.stem}.cog.tif"
  make_cog = True if not cog_path.exists() else False

  if action == IndexAction.REINDEX_FILENAME and old_stem is not None:
    old_cog = cog_dir / f"{old_stem}.cog.tif"
    if old_cog.exists():
      old_cog.rename(cog_path)
      make_cog = False

  if make_cog:
    generate_cog(image_file, cog_path)


def index_image(
  catalog_id: UUID, image_dir: Path, file: Path, thumbnail_minsize: tuple[int, int]
):
  image_hash = hash_geotiff(file)
  action, old_stem = check_image(file, image_hash)

  if action == IndexAction.INDEXED:
    return None, None

  if action == IndexAction.DUPLICATE:
    # TODO: handle duplicates
    return None, None

  metadata = parse_image_metadata(file)
  relative_directory = file.parent.relative_to(image_dir)
  index_row, radiometric_row = parse_image_info(
    metadata, image_hash, catalog_id, file, relative_directory
  )

  if action == IndexAction.REINDEX_PARENT:
    return index_row, radiometric_row

  process_thumbnail(file, metadata, index_row, action, old_stem, thumbnail_minsize)
  process_cog(file, action, old_stem)

  return index_row, radiometric_row


def index_images(
  catalog_id: UUID,
  thumbnail_minsize: tuple[int, int] = (600, 400),
  progress_callback: Optional[Callable[[int, int, str], None]] = None,
):
  extensions = {".tif", ".tiff"}
  query = (
    Query()
    .select("path")
    .from_(CatalogTable._table_name)
    .where("id = ?", catalog_id.bytes)
  )

  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    catalog_record = db.select_records(CatalogTable, query)
    if not catalog_record:
      from pprint import pformat

      catalogs = get_catalog_edit_data()
      raise ValueError(
        f"Failed to get path for catalog id {id}. Registered catalogs\n",
        f"{pformat(catalogs, indent=2)}",
      )

    image_dir = cast(Path, catalog_record[0]["path"])

    files = [
      f
      for f in image_dir.rglob("*")
      if f.suffix.lower() in extensions and not f.name.lower().endswith("_browser.tif")
    ]
    total = len(files)

    image_index: list[ImageIndexTable] = []
    radiometric_index: list[RadiometricParamsTable] = []

    for i, file in enumerate(files, start=1):
      if progress_callback:
        progress_callback(i, total, str(file.relative_to(image_dir)))

      index_row, radiometric_row = index_image(
        catalog_id, image_dir, file, thumbnail_minsize
      )

      if index_row is not None:
        image_index.append(index_row)

      if radiometric_row is not None:
        radiometric_index.append(radiometric_row)

    # Upsert index
    update_sql = """
      UPDATE SET
        catalog = excluded.catalog,
        relative_path = excluded.relative_path,
        filename = excluded.filename,
        filetype = excluded.filetype
    """
    on_conflict = OnConflict(index="id", action=update_sql)
    db.insert_models(image_index, on_conflict)

    current_timestamp = datetime.now(timezone.utc)
    update_index_time(db, catalog_id, current_timestamp)

    if radiometric_index:
      db.insert_models(radiometric_index)


class ImageQuery(TypedDict, total=False):
  wkt: Optional[str]
  area_id: Optional[str]
  filename: Optional[str]
  min_coverage: Optional[int]
  min_iirs: Optional[float]
  max_gsd: Optional[float]
  date_start: Optional[int]
  date_end: Optional[int]


def search_images(payload: ImageQuery):
  wkt = payload.get("wkt")
  area_id = payload.get("area_id")
  if area_id is not None:
    wkt = get_area_wkt(area_id)["geometry"]

  return get_images_by_intersection(wkt, payload)


def get_images_by_intersection(polygon_wkt: Optional[str], payload: ImageQuery):
  columns = ImageIndexTable.column_sql()
  query = Query().from_(ImageIndexTable._table_name).select(*columns)

  filename = payload.get("filename")
  if filename is not None:
    query.where("filename = ?", filename)

  min_coverage = payload.get("min_coverage")
  if min_coverage is not None:
    query.where("coverage >= ?", min_coverage)

  min_iirs = payload.get("min_iirs")
  if min_iirs is not None:
    query.where("interpretation_rating >= ?", min_iirs)

  max_gsd = payload.get("max_gsd")
  if max_gsd is not None:
    query.where("ground_sample_distance_row <= ?", max_gsd)
    query.where("ground_sample_distance_col <= ?", max_gsd)

  date_start = payload.get("date_start")
  date_end = payload.get("date_end")
  if date_start is not None and date_end is not None:
    query.where("datetime_collected >= ?", date_start)
    query.where("datetime_collected <= ?", date_end)

  if polygon_wkt is not None:
    polygon_cte = (
      Query()
      .select("geom", "ST_Area(geom) AS area")
      .from_("(SELECT ST_GeomFromText(?, 4326) AS geom) AS tmp", polygon_wkt)
    )

    query.with_("poly", polygon_cte).cross_join("poly").where(
      "ST_Intersects(footprint, poly.geom)"
    ).select("ST_Area(ST_Intersection(footprint, poly.geom)) / poly.area AS coverage")

  print(query.build())
  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    results = db.select_records(ImageIndexTable, query, True)

  return {"wkt": polygon_wkt, "images": results}


def get_image_info(id: bytes) -> dict:
  query = (
    Query()
    .select(
      "filename",
      "datetime_collected",
      "classification",
      "image_type",
      "band_statistics",
    )
    .from_(ImageIndexTable._table_name)
    .where("id = ?", id)
  )

  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    info = db.select_records(ImageIndexTable, query, to_json=True)
    return info[0]
