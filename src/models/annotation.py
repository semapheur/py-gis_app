import json
import re
import uuid
from sqlite3 import Row
from typing import Literal, TypedDict, Union

from src.const import ANNOTATION_DB, ATTRIBUTE_DB
from src.hashing import uuid_bytes_to_str
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


def update_annotations(payloads: list[AnnotationUpdate]):
  wkt_pattern = re.compile(r"^(?:SRID=\d+;)?(POINT|POLYGON|MULTIPOLYGON)", re.I)

  upsert_models: dict[str, list[type[Model]]] = {"equipment": [], "activity": []}

  update_sql = """UPDATE SET
    equipment = excluded.equipment,
    confidence = excluded.confidence,
    status = excluded.status,
    geometry = excluded.geometry,
    modifiedByUserId = excluded.modifiedByUserId,
    modifiedAtTimestamp = excluded.modifiedAtTimestamp
  """

  on_conflict = OnConflict(index="id", action=update_sql)

  for payload in payloads:
    annotation_type = payload.get("type")

    if annotation_type not in upsert_models:
      raise ValueError(f"Invalid annotation type: {annotation_type}")

    data = payload.get("data")
    if data is None:
      raise ValueError("Missing annotation data")

    geometry_wkt = data.get("geometry", "")
    match = wkt_pattern.search(geometry_wkt)
    if match is None:
      raise ValueError(f"Invalid WKT: {geometry_wkt}")

    geometry = match.group(1)
    model_cls = equipment_annotation_model(geometry)
    upsert_models[annotation_type].append(model_cls.from_dict(data, True))

  with SqliteDatabase(ANNOTATION_DB, spatial=True) as db:
    for models in upsert_models.values():
      if not models:
        continue

      db.insert_models(models, on_conflict)


def delete_annotations(payload: dict[str, list[str]]):
  supported_keys = {"equipment": {"point", "polygon"}, "activity": {"multipolygon"}}

  def parse_key(key: str) -> tuple[str, str]:
    try:
      annotation_type, geometry = key.split("_", 1)

    except ValueError:
      raise ValueError(f"Invalid payload key format: {key}")

    if annotation_type not in supported_keys:
      raise ValueError(f"Unsupported annotation type: {annotation_type}")

    if geometry not in supported_keys[annotation_type]:
      raise ValueError(f"Unsupported geometry type for '{annotation_type}': {geometry}")

    return annotation_type, geometry

  def resolve_model(annotation_type: str, geometry: str):
    if annotation_type == "equipment":
      return equipment_annotation_model(geometry)

    if annotation_type == "activity":
      raise NotImplementedError("Annotation deletion not implemented for activity")

    raise RuntimeError(f"Invalid annotation type: {annotation_type}")

  with SqliteDatabase(ANNOTATION_DB, spatial=True) as db:
    for key, ids in payload.items():
      annotation_type, geometry = parse_key(key)
      model = resolve_model(annotation_type, geometry)

      uuids = [uuid.UUID(u) for u in ids]
      db.delete_by_ids(model, uuids)


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
      "id": uuid_bytes_to_str(r["id"]),
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
      "metaData": {
        "createdByUserId": r["createdByUserId"],
        "modifiedByUserId": r["modifiedByUserId"],
        "createdAtTimestamp": r["createdAtTimestamp"],
        "modifiedAtTimestamp": r["modifiedAtTimestamp"],
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
      a.equipment_status.text AS status_label,
      ep.createdByUserId AS createdByUserId,
      ep.modifiedByUserId AS modifiedByUserId,
      ep.createdAtTimestamp AS createdAtTimestamp,
      ep.modifiedAtTimestamp AS modifiedAtTimestamp
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


class ConvertAnnotation(TypedDict):
  id: str
  geometry: str


def convert_annotation(payload: ConvertAnnotation):
  sql = """
    INSERT INTO equipment_polygon(
      id,
      image,
      equipment,
      status,
      createdByUserId,
      modifiedByUserId,
      createdAtTimestamp,
      modifiedAtTimestamp,
      geometry
    )
    SELECT
      id,
      image,
      equipment,
      status,
      createdByUserId,
      modifiedByUserId,
      createdAtTimestamp,
      modifiedAtTimestamp,
      ST_GeomFromText(:geometry, 4326)
    FROM equipment_point
    WHERE id = :id;

    DELETE FROM equipment_point
    WHERE id = :id;
  """

  params = {"id": payload["id"], "geometry": payload["geometry"]}

  with SqliteDatabase(ANNOTATION_DB, spatial=True) as db:
    cursor = db.conn.cursor()
    cursor.execute(sql, params)
