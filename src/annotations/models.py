import json
import re
from sqlite3 import Row
from typing import Literal, TypedDict, Union

from src.const import ANNOTATION_DB, ATTRIBUTE_DB
from src.hashing import encode_sha256_to_b64, uuid_bytes_to_str
from src.spatialite import (
  Field,
  Model,
  OnConflict,
  SqliteDatabase,
  datetime_field,
  hash_field,
  uuid_field,
)

EquipmentGeometry = Literal["POINT", "POLYGON"]


def equipment_annotation_model(geometry_type: EquipmentGeometry):
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


def get_annotations(image_id: bytes):
  return [
    *get_annotations_by_geometry(image_id, "POINT"),
    *get_annotations_by_geometry(image_id, "POLYGON"),
  ]


def get_annotations_by_geometry(image_id: bytes, geometry: EquipmentGeometry):
  def map_row(row: Row):
    r = dict(row)

    label = "\n".join(
      [
        r["equipment_label"],
        r["confidence_label"],
        r["status_label"],
      ]
    )

    return {
      "id": encode_sha256_to_b64(r["id"]),
      "geometry": json.loads(r["geometry"]),
      "label": label,
      "data": {
        "equipment": {
          "id": uuid_bytes_to_str(r["equipment_id"]),
          "label": r["equipment_label"],
        },
        "confidence": {
          "id": uuid_bytes_to_str(r["confidence_id"]),
          "label": r["confidence_label"],
        },
        "status": {
          "id": uuid_bytes_to_str(r["status_id"]),
          "label": r["status_label"],
        },
      },
    }

  attach_sql = f"ATTACH DATABASE '{ATTRIBUTE_DB}' AS a"
  detach_sql = "DETACH DATABASE a"
  select_sql = f"""
    SELECT
      ep.id AS id,
      AsGeoJSON(ep.geometry) AS geometry,
      ep.equipment AS equipment_id,
      a.equipment.displayName AS equipment_label,
      ep.confidence AS confidence_id,
      a.observation_confidence.text AS confidence_label,
      ep.status AS status_id,
      a.equipment_status.text AS status_label
    FROM equipment_{geometry.lower()} AS ep
    JOIN a.equipment
      ON a.equipment.id = ep.equipment
    JOIN a.observation_confidence
      ON a.observation_confidence.id = ep.confidence
    JOIN a.equipment_status
      ON a.equipment_status.id = ep.status
    WHERE ep.image = :image
  """
  params = {"image": image_id}

  with SqliteDatabase(ANNOTATION_DB, spatial=True) as db:
    db.conn.row_factory = Row
    cursor = db.conn.cursor()

    cursor.execute(attach_sql)

    try:
      return [map_row(r) for r in cursor.execute(select_sql, params)]

    finally:
      cursor.execute(detach_sql)
