import json
import math
from pathlib import Path
from typing import Optional, TypeAlias, TypedDict, Union, cast

from .gdal_utils import gdalinfo
from .math_utils import dot, norm
from .sicd_model import Sicd, SicdObject
from .spatialite import Field, Model, insert_records, spatialite_connect


class ImageIndexTable(Model):
  table_name = "images"
  id = Field(int, primary_key=True)
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
  n = (point[0] / n_mag, point[1] / n_mag, point[2] / n_mag)

  udotn = dot(unit_vector, n)

  ground_factor = math.sqrt(1.0 - udotn**2)

  return sample_spacing * ground_factor


def sicd_metadata(path: Path) -> Union[Sicd, None]:
  metadata = gdalinfo(path)

  sicd_text = metadata.get("metadata", {}).get("", {}).get("SICD_METADATA")

  if sicd_text is not None:
    sicd = cast(SicdObject, json.loads(sicd_text))
    return sicd["metadata"]

  return None


def parse_image_metadata(file_path: Path) -> ImageIndexRow:
  if not file_path.exists():
    raise FileNotFoundError(f"File not found: {str(file_path)}")

  extensions = {".tiff", ".tif"}
  if file_path.suffix.lower() not in extensions:
    raise ValueError(f"Input file must be .tif(f), got: {file_path.suffix}")

  sicd = sicd_metadata(file_path)
  if sicd is None:
    raise ValueError()

  collection_info = sicd["CollectionInfo"]
  geo_data = sicd["GeoData"]
  timeline = sicd["Timeline"]
  scpcoa = sicd["SCPCOA"]
  sensor_name = collection_info["CollectorName"]
  classification = collection_info["Classification"]
  interpretation_rating = collection_info.get("Parameters", {}).get("PREDICTED_RNIIRS")

  image_corners = geo_data["ImageCorners"]
  points = (f"{corner['Lat']} {corner['Lon']}" for corner in image_corners)
  footprint = f"POLYGON(({', '.join(points)}))"
  datetime_collected = timeline["CollectStart"]
  look_angle = 90.0 - scpcoa["IncidenceAng"]
  azimuth_angle = scpcoa["AzimAng"]

  scp_obj = geo_data["SCP"]["ECF"]
  scp = (scp_obj["X"], scp_obj["Y"], scp_obj["Z"])

  grid_row = sicd["Grid"]["Row"]
  sample_spacing_x = grid_row["SS"]
  unit_vec_obj_x = grid_row["UVectECF"]
  unit_vec_x = (unit_vec_obj_x["X"], unit_vec_obj_x["Y"], unit_vec_obj_x["Z"])
  gsd_x = ground_sample_distance(sample_spacing_x, unit_vec_x, scp)

  grid_col = sicd["Grid"]["Col"]
  sample_spacing_y = grid_col["SS"]
  unit_vec_obj_y = grid_col["UVectECF"]
  unit_vec_y = (unit_vec_obj_y["X"], unit_vec_obj_y["Y"], unit_vec_obj_y["Z"])
  gsd_y = ground_sample_distance(sample_spacing_y, unit_vec_y, scp)

  return ImageIndexRow(
    filename=file_path.name,
    filetype=file_path.suffix,
    classification=classification,
    datetime_collected=datetime_collected,
    sensor_name=sensor_name,
    sensor_type="",
    footprint=footprint,
    look_angle=look_angle,
    azimuth_angle=azimuth_angle,
    ground_sample_distance_row=gsd_x,
    ground_sample_distance_col=gsd_y,
    interpretation_rating=interpretation_rating,
  )


def create_image_index_table(db_path: Path):
  with spatialite_connect(db_path) as db:
    cursor = db.cursor()
    cursor.execute(ImageIndexTable.create_table_sql())

    for sql in ImageIndexTable.add_geometry_sql():
      cursor.execute(sql)


def index_images(folder: Path):
  if not folder.exists() or not folder.is_dir():
    raise FileNotFoundError(f"Invalid folder path: {folder}")
  extensions = {".tif", ".tiff"}

  image_index: list[ImageIndexRow] = []
  for file in folder.rglob("*"):
    if file.suffix.lower() not in extensions:
      continue

    image_index.append(parse_image_metadata(file))

  db_path = Path("data/index.db")
  if not db_path.exists():
    create_image_index_table(db_path)

  with spatialite_connect(db_path) as db:
    insert_records(db, cast(str, ImageIndexTable.table_name), image_index, "footprint")
