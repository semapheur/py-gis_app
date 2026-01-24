import re
from typing import Literal, TypedDict, Union

from src.const import ANNOTATION_DB
from src.spatialite import (
  Field,
  Model,
  OnConflict,
  SqliteDatabase,
  datetime_field,
  hash_field,
  uuid_field,
)


def equipment_annotation_model(geometry_type: Literal["POINT", "POLYGON"]):
  table_name = f"equipment_{geometry_type.lower()}"

  class EquipmentAnnotation(Model):
    _table_name = table_name
    id = uuid_field(True)
    image = hash_field(False)
    equipment = uuid_field(False)
    confidence = uuid_field(False)
    status = uuid_field(False)
    geometry = Field(str, geometry_type=geometry_type)
    createdByUserId = Field(str)
    modifiedByUserId = Field(str)
    createdAtTimestamp = datetime_field(False)
    modifiedAtTimestamp = datetime_field(True)

  EquipmentAnnotation.__name__ = f"{table_name.title().replace('_', '')}Table"
  return EquipmentAnnotation


def create_annotation_tables():
  geometries = ("POINT", "POLYGON")
  with SqliteDatabase(ANNOTATION_DB, spatial=True) as db:
    for g in geometries:
      model = equipment_annotation_model(g)
      db.create_table(model)


class AnnotationUpdate(TypedDict):
  type: Literal["activity", "equipment"]
  data: dict[str, Union[int, str, None]]


def update_annotation(payload: AnnotationUpdate):
  annotation_type = payload.pop("type", None)
  if annotation_type is None or annotation_type not in ("equipment", "activity"):
    raise ValueError(f"Annotation type missing in payload: {payload}")

  data = payload.get("data")
  if not data:
    raise ValueError(f"Annotation data missing in payload: {payload}")

  geometry_wkt = data.get("geometry", "")
  match = re.search("^(POINT|POLYGON)", geometry_wkt)
  if match is None:
    raise ValueError(f"Invalid WKT: {geometry_wkt}")

  geometry = match.group()
  model = equipment_annotation_model(geometry)

  update_sql = """UPDATE SET
    equipment = excluded.equipment,
    confidence = excluded.confidence,
    status = excluded.status,
    geometry = excluded.geometry,
    modifiedByUserId = excluded.modifiedByUserId,
    modifiedAtTimestamp = excluded.modifiedAtTimestamp
  """

  upsert_model = [model.from_dict(data, True)]
  on_conflict = OnConflict(index="id", action=update_sql)

  with SqliteDatabase(ANNOTATION_DB, spatial=True) as db:
    db.insert_models(upsert_model, on_conflict)
