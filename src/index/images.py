import json
import math
import tempfile
import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal, TypeAlias, Union, cast

from src.const import INDEX_DB, STATIC_DIR
from src.gdal_utils import (
  CogOptions,
  GdalTranslateOptions,
  GdalWarpOptions,
  gdal_translate,
  gdalinfo,
  gdalwarp,
)
from src.hashing import hash_geotiff
from src.index.catalog import CatalogTable, get_catalogs
from src.index.radiometric import NoiseParameters, RadiometricParamsTable
from src.math_utils import dot, norm
from src.sicd_model import SicdObject
from src.spatialite import (
  DATETIME_FIELD,
  HASH_FIELD,
  ColumnType,
  Field,
  JoinClause,
  Model,
  OnConflict,
  SpatialDatabase,
)

Vec3: TypeAlias = tuple[float, float, float]


class ImagerySensorType(Enum):
  EO = "eo"
  SAR = "sar"


class ImageryType(str, Enum):
  GRD = "grd"
  PAN = "pan"
  MS = "ms"
  SLC = "slc"


class ImageIndexTable(Model):
  table_name = "images"
  id = HASH_FIELD
  catalog = Field(int, nullable=False)
  relative_path = Field(
    Path,
    sql_type=ColumnType.TEXT,
    nullable=False,
    to_sql=lambda x: str(x),
    to_python=lambda x: Path(x),
    to_json=lambda x: str(x),
  )
  filename = Field(str, nullable=False)
  filetype = Field(str, nullable=False)
  classification = Field(str)
  datetime_collected = DATETIME_FIELD
  sensor_name = Field(str)
  sensor_type = Field(
    ImagerySensorType,
    ColumnType.TEXT,
    to_sql=lambda x: x.value,
    to_python=lambda x: ImagerySensorType(x),
    to_json=lambda x: x.value if isinstance(x, ImagerySensorType) else x,
  )
  image_type = Field(
    ImageryType,
    ColumnType.TEXT,
    to_sql=lambda x: x.value,
    to_python=lambda x: ImageryType(x),
    to_json=lambda x: x.value if isinstance(x, ImageryType) else x,
  )
  footprint = Field(str, geometry_type="POLYGON")
  look_angle = Field(float)
  azimuth_angle = Field(float)
  ground_sample_distance_row = Field(float)
  ground_sample_distance_col = Field(float)
  interpretation_rating = Field(float)


def ground_sample_distance(
  sample_spacing: float, unit_vector: Vec3, point: Vec3
) -> float:
  n_mag = norm(point)
  surface_normal = (point[0] / n_mag, point[1] / n_mag, point[2] / n_mag)
  udotn = dot(unit_vector, surface_normal)
  ground_factor = math.sqrt(1.0 - udotn**2)

  return sample_spacing * ground_factor


def tiff_metadata(
  gdal_info: dict, schema: Literal["SICD_METADATA", "TIFFTAG_IMAGEDESCRIPTION"]
) -> Union[dict, None]:
  metadata_text = gdal_info.get("metadata", {}).get("", {}).get(schema)

  if metadata_text is not None:
    return json.loads(metadata_text)

  return None


def detect_image_type(
  gdal_info: dict,
) -> tuple[ImagerySensorType, ImageryType]:
  metadata = gdal_info.get("metadata", {}).get("", {})
  bands = gdal_info.get("bands")
  if bands is None:
    raise ValueError("'bands' missing from gdalinfo")

  complex_bands = [band.get("type", "").lower().startswith("c") for band in bands]
  if any(complex_bands):
    return (ImagerySensorType.SAR, ImageryType.SLC)

  if "SICD_METADATA" in metadata:
    return (ImagerySensorType.SAR, ImageryType.GRD)

  num_bands = len(bands)
  if num_bands == 1:
    return (ImagerySensorType.EO, ImageryType.PAN)

  return (ImagerySensorType.EO, ImageryType.MS)


def parse_image_metadata(
  gdal_info: dict,
  hash: bytes,
  catalog_id: int,
  file_path: Path,
  relative_directory: Path,
) -> tuple[ImageIndexTable, Union[RadiometricParamsTable, None]]:
  sensor_type, image_type = detect_image_type(gdal_info)

  sicd_obj = tiff_metadata(gdal_info, "SICD_METADATA")

  if sicd_obj is None:
    raise ValueError(f"No SICD metadata found for {str(file_path)}")

  sicd = cast(SicdObject, sicd_obj)["metadata"]

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
  points = (f"{corner['Lon']} {corner['Lat']}" for corner in image_corners)
  footprint = f"POLYGON(({', '.join(points)}))"

  datetime_collected = datetime.fromisoformat(timeline["CollectStart"])
  look_angle = 90.0 - scpcoa["IncidenceAng"]
  azimuth_angle = scpcoa["AzimAng"]

  plane = sicd["RadarCollection"].get("Area", {}).get("Plane", {})

  gsd_row = plane.get("XDir", {}).get(
    "LineSpacing", tifftag.get("ground_range_resolution")
  )
  gsd_col = plane.get("YDir", {}).get(
    "SampleSpacing", tifftag.get("ground_azimuth_resolution")
  )

  data = {
    "id": hash,
    "catalog": catalog_id,
    "relative_path": relative_directory,
    "filename": file_path.stem,
    "filetype": file_path.suffix,
    "classification": classification,
    "datetime_collected": datetime_collected,
    "sensor_name": sensor_name,
    "sensor_type": sensor_type,
    "image_type": image_type,
    "footprint": footprint,
    "look_angle": look_angle,
    "azimuth_angle": azimuth_angle,
    "ground_sample_distance_row": gsd_row,
    "ground_sample_distance_col": gsd_col,
    "interpretation_rating": interpretation_rating,
  }

  index_row = ImageIndexTable()
  for key, value in data.items():
    setattr(index_row, key, value)

  if image_type != ImageryType.SLC:
    return index_row, None

  radiometric_metadata = sicd.get("Radiometric", {})
  if not radiometric_metadata:
    return index_row, None

  noise_params = radiometric_metadata.get("NoiseLevel", {})
  noise_data = (
    NoiseParameters(
      type=noise_params["NoiseLevelType"], poly=noise_params["NoisePoly"]["Coefs"]
    )
    if noise_params
    else None
  )

  radiometric_params = {
    "id": hash,
    "noise": noise_data,
    "sigma0": radiometric_metadata.get("SigmaZeroSFPoly", {}).get("Coefs", []),
    "beta0": radiometric_metadata.get("BetaZeroSFPoly", {}).get("Coefs", []),
    "gamma0": radiometric_metadata.get("GammaZeroSFPoly", {}).get("Coefs", []),
  }

  radiometric_row = RadiometricParamsTable()
  for key, value in radiometric_params.items():
    setattr(radiometric_row, key, value)

  return index_row, radiometric_row


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
  with SpatialDatabase(INDEX_DB) as db:
    derived_columns = {
      "path": "concat(catalog.path, '/', images.relative_path, '/', images.filename, images.filetype)",
    }
    join = JoinClause(
      join_type="INNER", expression="catalog ON catalog.id = images.catalog"
    )
    where = "images.id = :id"
    params = {"id": hash}

    result = db.select_records(
      ImageIndexTable, derived=derived_columns, join=join, where=where, params=params
    )

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

  cog_dir = STATIC_DIR / "cog"
  cog_dir.mkdir(exist_ok=True)

  thumbnail_dir = STATIC_DIR / "thumbnails"
  thumbnail_dir.mkdir(exist_ok=True)

  with SpatialDatabase(INDEX_DB) as db:
    db.create_table(ImageIndexTable)
    db.create_table(RadiometricParamsTable)

    catalog_record = db.select_records(
      CatalogTable,
      columns=("path",),
      where="id = :id",
      params={"id": catalog_id},
    )
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

    if radiometric_index:
      db.insert_models(radiometric_index)


def get_images_by_intersection(polygon_wkt: str):
  with SpatialDatabase(INDEX_DB) as db:
    where = "ST_Intersects(footprint, poly.geom)"
    derived = {"coverage": "ST_Area(ST_Intersection(footprint, poly.geom)) / poly.area"}
    with_clause = "poly AS (SELECT geom, ST_Area(geom) AS area FROM (SELECT ST_GeomFromText(:polygon, 4326) AS geom) AS tmp)"
    join = JoinClause(join_type="CROSS", expression="poly")
    params = {"polygon": polygon_wkt}

    return db.select_records(
      ImageIndexTable,
      columns="*",
      with_clause=with_clause,
      geo_format="AsGeoJSON",
      derived=derived,
      join=join,
      where=where,
      params=params,
    )


def get_image_info(id: bytes) -> dict:
  with SpatialDatabase(INDEX_DB) as db:
    where = "id = :id"
    params = {"id": id}

    info = db.select_records(
      ImageIndexTable,
      columns=(
        "filename",
        "image_type",
      ),
      where=where,
      params=params,
    )
    return info[0]
