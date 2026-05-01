import json
import tempfile
import warnings
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal, Optional, TypedDict, Union, cast

from src.bootstrap import get_settings
from src.gdal_utils import (
  CogOptions,
  GdalTranslateOptions,
  GdalWarpOptions,
  gdal_translate,
  gdalinfo,
  gdalwarp,
)
from src.hashing import hash_geotiff
from src.index.catalog import CatalogTable, get_catalogs, update_index_time
from src.index.radiometric import (
  NoiseParameters,
  RadiometricParamsTable,
  generate_intensity_vrt,
)
from src.models.areas import get_area_wkt
from src.sicd_model import SicdObject, sicd_polygon_wkt
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


def create_index_table():
  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    db.create_table(ImageIndexTable)


def detect_image_type(
  gdal_info: dict,
) -> tuple[ImagerySensorType, ImageryType]:
  bands = gdal_info.get("bands")
  if bands is None:
    raise ValueError("'bands' missing from gdalinfo")

  metadata = gdal_info.get("metadata", {}).get("", {})
  complex_bands = [band.get("type", "").lower().startswith("c") for band in bands]
  if any(complex_bands):
    return (ImagerySensorType.SAR, ImageryType.SLC)

  if "SICD_METADATA" in metadata:
    return (ImagerySensorType.SAR, ImageryType.GRD)

  num_bands = len(bands)
  if num_bands == 1:
    return (ImagerySensorType.EO, ImageryType.PAN)

  return (ImagerySensorType.EO, ImageryType.MS)


def tiff_metadata(
  gdal_info: dict, schema: Literal["SICD_METADATA", "TIFFTAG_IMAGEDESCRIPTION"]
) -> Union[dict, None]:
  metadata_text = gdal_info.get("metadata", {}).get("", {}).get(schema)

  if metadata_text is not None:
    return json.loads(metadata_text)

  return None


def make_index_row(data: dict) -> ImageIndexTable:
  row = ImageIndexTable()
  for key, value in data.items():
    setattr(row, key, value)

  return row


def make_radiometric_row(
  sicd: dict, image_hash: bytes
) -> RadiometricParamsTable | None:
  radiometric_metadata = sicd.get("Radiometric", {})
  if not radiometric_metadata:
    return None

  noise_params = radiometric_metadata.get("NoiseLevel", {})
  noise_data = (
    NoiseParameters(
      type=noise_params["NoiseLevelType"],
      poly=noise_params["NoisePoly"]["Coefs"],
    )
    if noise_params
    else None
  )

  radiometric_params = {
    "id": image_hash,
    "noise": noise_data,
    "sigma0": radiometric_metadata.get("SigmaZeroSFPoly", {}).get("Coefs", []),
    "beta0": radiometric_metadata.get("BetaZeroSFPoly", {}).get("Coefs", []),
    "gamma0": radiometric_metadata.get("GammaZeroSFPoly", {}).get("Coefs", []),
  }

  row = RadiometricParamsTable()
  for key, value in radiometric_params.items():
    setattr(row, key, value)

  return row


def find_tile_for_file(isd: dict, stem: str) -> dict:
  for tile in isd.get("tiles", []):
    if Path(tile.get("filename", "")).stem == stem:
      return tile
  return {}


def isd_polygon_wkt(tile: dict) -> str:
  points = (
    f"{tile['ullon']} {tile['ullat']}",
    f"{tile['urlon']} {tile['urlat']}",
    f"{tile['lrlon']} {tile['lrlat']}",
    f"{tile['lllon']} {tile['lllat']}",
    f"{tile['ullon']} {tile['ullat']}",
  )
  return f"POLYGON(({', '.join(points)}))"


def parse_sicd_metadata(gdal_info: dict, sicd_obj: SicdObject):

  sicd = sicd_obj["metadata"]

  tifftag = tiff_metadata(gdal_info, "TIFFTAG_IMAGEDESCRIPTION") or {}
  tifftag = tifftag.get("collect", {}).get("image", {})

  collection_info = sicd["CollectionInfo"]
  geo_data = sicd["GeoData"]
  timeline = sicd["Timeline"]
  scpcoa = sicd["SCPCOA"]

  sensor_name = collection_info["CollectorName"]
  classification = collection_info["Classification"]
  interpretation_rating = collection_info.get("Parameters", {}).get("PREDICTED_RNIIRS")

  image_corners = geo_data["ImageCorners"]
  footprint = sicd_polygon_wkt(image_corners)

  datetime_collected = datetime.fromisoformat(timeline["CollectStart"])
  look_angle = 90.0 - scpcoa["IncidenceAng"]
  azimuth_angle = scpcoa["AzimAng"]

  plane = sicd["RadarCollection"].get("Area", {}).get("Plane", {})

  gsd_row = plane.get("XDir", {}).get("LineSpacing") or tifftag.get(
    "ground_range_resolution"
  )

  gsd_col = plane.get("YDir", {}).get("SampleSpacing") or tifftag.get(
    "ground_azimuth_resolution"
  )

  return {
    "classification": classification,
    "datetime_collected": datetime_collected,
    "sensor_name": sensor_name,
    "footprint": footprint,
    "look_angle": look_angle,
    "azimuth_angle": azimuth_angle,
    "ground_sample_distance_row": gsd_row,
    "ground_sample_distance_col": gsd_col,
    "interpretation_rating": interpretation_rating,
  }


def parse_image_metadata(
  gdal_info: dict,
  hash: bytes,
  catalog_id: int,
  file_path: Path,
  relative_directory: Path,
) -> tuple[ImageIndexTable, Union[RadiometricParamsTable, None]]:

  sensor_type, image_type = detect_image_type(gdal_info)

  base_data = {
    "id": hash,
    "catalog": catalog_id,
    "relative_path": relative_directory,
    "filename": file_path.stem,
    "filetype": file_path.suffix,
    "sensor_type": sensor_type,
    "image_type": image_type,
  }

  isd = gdal_info.get("isd")
  if isd is not None:
    image_info = isd.get("image", {})
    tile = find_tile_for_file(isd, file_path.stem)

    datetime_collected = datetime.fromisoformat(image_info.get("acquisition_time"))
    footprint = isd_polygon_wkt(tile)

    data = {
      **base_data,
      "classification": "UNCLASSIFIED",
      "datetime_collected": datetime_collected,
      "sensor_name": image_info.get("satellite_id"),
      "footprint": footprint,
      "look_angle": image_info.get("mean_off_nadir"),
      "azimuth_angle": image_info.get("mean_sat_azimuth"),
      "ground_sample_distance_row": image_info.get("mean_gsd_row"),
      "ground_sample_distance_col": image_info.get("mean_gsd_col"),
      "interpretation_rating": image_info.get("pniirs"),
    }

    index_row = make_index_row(data)
    return index_row, None

  sicd_obj = tiff_metadata(gdal_info, "SICD_METADATA")

  if sicd_obj is not None:
    sicd_data = parse_sicd_metadata(gdal_info, cast(SicdObject, sicd_obj))

    data = {**base_data, **sicd_data}
    index_row = make_index_row(data)

    if image_type != ImageryType.SLC:
      return index_row, None

    radiometric_row = make_radiometric_row(sicd_obj["metadata"], hash)
    return index_row, radiometric_row


def generate_cog(
  image_path: Path,
  cog_path: Path,
  gdal_info: dict,
  image_type: ImageryType,
):
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

  if image_type == ImageryType.SLC:
    gdalwarp(
      image_path,
      cog_path,
      options,
    )
    return

  with tempfile.TemporaryDirectory() as tmpdir:
    tmp_intensity = Path(tmpdir) / f"{image_path.stem}_intensity.tif"
    generate_intensity_vrt(image_path, tmp_intensity, gdal_info)
    gdalwarp(tmp_intensity, cog_path, options)


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


def index_images(
  catalog_id: int,
  thumbnail_minsize: tuple[int, int] = (600, 400),
):
  extensions = {".tif", ".tiff"}

  cog_dir = app_settings.STATIC_DIR / "cog"
  cog_dir.mkdir(exist_ok=True)

  thumbnail_dir = app_settings.STATIC_DIR / "thumbnails"
  thumbnail_dir.mkdir(exist_ok=True)

  query = (
    Query().select("path").from_(CatalogTable._table_name).where("id = ?", catalog_id)
  )

  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    catalog_record = db.select_records(CatalogTable, query)
    if not catalog_record:
      from pprint import pformat

      catalogs = get_catalogs()
      raise ValueError(
        f"Failed to get path for catalog id {id}. Registered catalogs\n",
        f"{pformat(catalogs, indent=2)}",
      )

    image_dir = cast(Path, catalog_record[0]["path"])

    image_index: list[ImageIndexTable] = []
    radiometric_index: list[RadiometricParamsTable] = []
    for file in image_dir.rglob("*"):
      if file.suffix.lower() not in extensions:
        continue

      image_hash = hash_geotiff(file)
      action, old_stem = check_image(file, image_hash)

      if action == IndexAction.INDEXED:
        continue

      if action == IndexAction.DUPLICATE:
        # TODO: handle duplicates
        continue

      info = gdalinfo(file)
      relative_directory = file.parent.relative_to(image_dir)
      index_row, radiometric_row = parse_image_metadata(
        info, image_hash, catalog_id, file, relative_directory
      )
      image_index.append(index_row)

      if radiometric_row is not None:
        radiometric_index.append(radiometric_row)

      if action == IndexAction.REINDEX_PARENT:
        continue

      # Create thumbnail
      thumbnail_path = thumbnail_dir / f"{file.stem}.png"
      make_thumbnail = True if not thumbnail_path.exists() else False
      if action == IndexAction.REINDEX_FILENAME:
        old_thumbnail = thumbnail_dir / f"{old_stem}.png"
        if old_thumbnail.exists():
          old_thumbnail.rename(thumbnail_path)
          make_thumbnail = False

      if make_thumbnail:
        image_size = info["size"]
        gsd = (
          getattr(index_row, "ground_sample_distance_row"),
          getattr(index_row, "ground_sample_distance_col"),
        )
        generate_thumbnail(file, thumbnail_path, gsd, image_size, thumbnail_minsize)

      # create cloud-optimized geotif (COG)
      cog_path = cog_dir / f"{file.stem}.cog.tif"
      make_cog = True if not cog_path.exists() else False
      if action == IndexAction.REINDEX_FILENAME:
        old_cog = cog_dir / f"{old_stem}.cog.tif"
        if old_cog.exists():
          old_cog.rename(cog_path)
          make_cog = False

      if make_cog:
        image_type = ImageryType(getattr(index_row, "image_type"))
        generate_cog(file, cog_path, info, image_type)

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
    poly_cte = (
      Query()
      .select("geom", "ST_Area(geom) AS area")
      .from_("(SELECT ST_GeomFromText(?, 4326) AS geom) AS tmp", polygon_wkt)
    )

    query.with_("poly", poly_cte).cross_join("poly").where(
      "ST_Intersects(footprint, poly.geom)"
    ).select("ST_Area(ST_Intersection(footprint, poly.geom)) / poly.area AS coverage")

  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    results = db.select_records(ImageIndexTable, query, True)

  return {"wkt": polygon_wkt, "images": results}


def get_image_info(id: bytes) -> dict:
  query = (
    Query()
    .select("filename", "image_type")
    .from_(ImageIndexTable._table_name)
    .where("id = ?", id)
  )

  with SqliteDatabase(app_settings.INDEX_DB, spatial=True) as db:
    info = db.select_records(ImageIndexTable, query)
    return info[0]
