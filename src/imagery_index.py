import json
import math
import os
from pathlib import Path
from typing import Literal, Optional, TypeAlias, TypedDict, Union, cast

from .env import load_env
from .gdal_utils import GdalTranslateOptions, gdal_translate, gdalinfo
from .geometry import Polygon
from .math_utils import dot, norm
from .sicd_model import SicdObject
from .spatialite import Field, Model, SpatialDatabase


class ImageIndexTable(Model):
  table_name = "images"
  id = Field(int, primary_key=True)
  directory = Field(str)
  filename = Field(str)
  filetype = Field(str)
  classification = Field(str)
  datetime_collected = Field(str)
  sensor_name = Field(str)
  sensor_type = Field(str)
  footprint = Field(str, geometry_type="POLYGON")
  look_angle = Field(float)
  azimuth_angle = Field(float)
  ground_sample_distance_row = Field(float)
  ground_sample_distance_col = Field(float)
  interpretation_rating = Field(float)


class ImageIndexRow(TypedDict):
  directory: str
  filename: str
  filetype: str
  classification: str
  datetime_collected: str
  sensor_name: str
  sensor_type: str
  footprint: str
  look_angle: float
  azimuth_angle: float
  ground_sample_distance_row: float
  ground_sample_distance_col: float
  interpretation_rating: Optional[float]


Vec3: TypeAlias = tuple[float, float, float]


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


def parse_image_metadata(
  info: dict, file_path: Path, relative_directory: Path
) -> ImageIndexRow:
  sicd_obj = tiff_metadata(info, "SICD_METADATA")

  if sicd_obj is None:
    raise ValueError(f"No SICD metadata found for {str(file_path)}")

  sicd = cast(SicdObject, sicd_obj)["metadata"]

  tifftag = tiff_metadata(info, "TIFFTAG_IMAGEDESCRIPTION") or {}
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
  datetime_collected = timeline["CollectStart"]
  look_angle = 90.0 - scpcoa["IncidenceAng"]
  azimuth_angle = scpcoa["AzimAng"]

  plane = sicd["RadarCollection"].get("Area", {}).get("Plane", {})

  gsd_row = plane.get("XDir", {}).get(
    "LineSpacing", tifftag.get("ground_range_resolution")
  )
  gsd_col = plane.get("YDir", {}).get(
    "SampleSpacing", tifftag.get("ground_azimuth_resolution")
  )

  return ImageIndexRow(
    directory=str(relative_directory),
    filename=file_path.stem,
    filetype=file_path.suffix,
    classification=classification,
    datetime_collected=datetime_collected,
    sensor_name=sensor_name,
    sensor_type="",
    footprint=footprint,
    look_angle=look_angle,
    azimuth_angle=azimuth_angle,
    ground_sample_distance_row=gsd_row,
    ground_sample_distance_col=gsd_col,
    interpretation_rating=interpretation_rating,
  )


def index_images(image_dir: Path, thumbnail_minsize: tuple[int, int] = (600, 400)):
  if not image_dir.exists() or not image_dir.is_dir():
    raise FileNotFoundError(f"Invalid folder path: {image_dir}")

  load_env()

  extensions = {".tif", ".tiff"}

  thumbnail_dir = Path(os.environ["STATIC_DIR"]) / "thumbnails"
  thumbnail_dir.mkdir(exist_ok=True)

  image_index: list[ImageIndexTable] = []
  for file in image_dir.rglob("*"):
    if file.suffix.lower() not in extensions:
      continue

    info = gdalinfo(file)
    relative_directory = file.parent.relative_to(image_dir)
    metadata = parse_image_metadata(info, file, relative_directory)

    row = ImageIndexTable()
    for key, value in metadata.items():
      setattr(row, key, value)

    image_index.append(row)

    thumbnail_path = thumbnail_dir / f"{file.stem}.png"

    width, height = info["size"]
    gsd_x = metadata["ground_sample_distance_row"]
    gsd_y = metadata["ground_sample_distance_col"]
    gsd = max(gsd_x, gsd_y)

    width = int(width * (gsd_x / gsd))
    height = int(height * (gsd_y / gsd))
    aspect = width / height
    min_width, min_height = thumbnail_minsize

    thumbnail_width = min_width if aspect < 1 else int(min_height * aspect)
    thumbnail_height = min_height if aspect > 1 else int(min_width * aspect)

    options = GdalTranslateOptions(outsize=(thumbnail_width, thumbnail_height))

    gdal_translate(
      input_path=file,
      output_path=thumbnail_path,
      output_format="PNG",
      options=options,
    )

  db_path = Path(os.getenv("DB_DIR", "db")) / "index.db"

  with SpatialDatabase(db_path) as db:
    db.create_table(ImageIndexTable)
    db.insert_models(image_index)


def select_images_by_intersection(db_path: Path, polygon: Polygon):
  with SpatialDatabase(db_path) as db:
    where = "ST_Intersects(footprint, poly.geom)"
    derived = {"coverage": "ST_Area(ST_Intersection(footprint, poly.geom)) / poly.area"}
    with_clause = "poly AS (SELECT geom, ST_Area(geom) AS area FROM (SELECT ST_GeomFromText(:polygon, 4326) AS geom) AS tmp)"
    cross_join = "poly"
    params = {"polygon": polygon.to_wkt()}

    return db.select_records(
      ImageIndexTable,
      with_clause=with_clause,
      geo_format="AsGeoJSON",
      derived=derived,
      cross_join=cross_join,
      where=where,
      params=params,
    )
