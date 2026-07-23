import json
import re
import uuid
from sqlite3 import Row
from typing import Literal, TypedDict, Union

from src.bootstrap import get_settings
from src.hashing import encode_sha256_to_b64, uuid_bytes_to_str
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import (
  DeleteQuery,
  SelectQuery,
  UnionQuery,
  UpdateQuery,
)
from src.sqlite.table import (
  Field,
  GeometryField,
  Table,
  datetime_field,
  hash_field,
  uuid_field,
)

EquipmentGeometry = Literal["POINT", "POLYGON"]

app_settings = get_settings()


def equipment_annotation_model(geometry_type: EquipmentGeometry):
  table_name = f"equipment_{geometry_type.lower()}"

  class EquipmentAnnotation(Table):
    _table_name = table_name
    id = uuid_field(True, False)
    image = hash_field(False)
    equipment = uuid_field(False, False)
    confidence = uuid_field(False, False)
    status = uuid_field(False, False)
    geometry = GeometryField(str, geometry_type=geometry_type)
    createdByUserId = Field(str)
    modifiedByUserId = Field(str)
    createdAtTimestamp = datetime_field(False)
    modifiedAtTimestamp = datetime_field(True)

  EquipmentAnnotation.__name__ = f"{table_name.title().replace('_', '')}Table"
  return EquipmentAnnotation


def create_annotation_tables():
  geometries = ("POINT", "POLYGON")
  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    for g in geometries:
      model = equipment_annotation_model(g)
      db.create_table(model)


class AnnotationUpdate(TypedDict):
  type: Literal["activity", "equipment"]
  data: dict[str, Union[int, str, None]]


def update_annotations(payloads: list[AnnotationUpdate]):
  wkt_pattern = re.compile(r"^(?:SRID=\d+;)?(POINT|POLYGON|MULTIPOLYGON)", re.I)

  upsert_models: dict[str, list[type[Table]]] = {"equipment": [], "activity": []}

  update_query = UpdateQuery().set_excluded(
    "equipment",
    "confidence",
    "status",
    "geometry",
    "modifiedByUserId",
    "modifiedAtTimestamp",
  )

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

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    for models in upsert_models.values():
      if not models:
        continue

      db.insert_models(models, "id", update_query)


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

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    for key, ids in payload.items():
      annotation_type, geometry = parse_key(key)
      model = resolve_model(annotation_type, geometry)

      uuids = [uuid.UUID(u) for u in ids]
      db.delete_by_ids(model, uuids)


def get_annotations_by_image(image_id: bytes):

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

  def build_subquery(geometry: EquipmentGeometry):
    return (
      SelectQuery()
      .select(
        "ea.id AS id",
        "AsGeoJSON(ea.geometry) AS geometry",
        "ea.equipment AS equipment_id",
        "ed.equipment.displayName AS equipment_label",
        "ea.confidence AS confidence_id",
        "a.observation_confidence.name AS confidence_label",
        "ea.status AS status_id",
        "a.equipment_status.name AS status_label",
        "ea.createdByUserId AS createdByUserId",
        "ea.modifiedByUserId AS modifiedByUserId",
        "ea.createdAtTimestamp AS createdAtTimestamp",
        "ea.modifiedAtTimestamp AS modifiedAtTimestamp",
      )
      .from_(f"equipment_{geometry.lower()} ea")
      .inner_join("ed.equipment", "ed.equipment.id = ea.equipment")
      .inner_join(
        "a.observation_confidence", "a.observation_confidence.id = ea.confidence"
      )
      .inner_join("a.equipment_status", "a.equipment_status.id = ea.status")
      .where("ea.image = ?", image_id)
    )

  attach_sql = (
    f"ATTACH DATABASE '{app_settings.EQUIPMENT_DB}' AS ed",
    f"ATTACH DATABASE '{app_settings.ATTRIBUTE_DB}' AS a",
  )
  detach_sql = ("DETACH DATABASE ed", "DETACH DATABASE a")

  geometries = ["POINT", "POLYGON"]
  subqueries = [build_subquery(g) for g in geometries]
  select_sql, params = UnionQuery(*subqueries).build()

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    db.conn.row_factory = Row
    cursor = db.conn.cursor()

    for statement in attach_sql:
      cursor.execute(statement)

    try:
      return [map_row(r) for r in cursor.execute(select_sql, params)]

    finally:
      for statement in detach_sql:
        cursor.execute(statement)


class GhostSearch(TypedDict):
  polygon_wkt: str
  datetime_collected: int
  future: bool


def get_annotation_ghosts(payload: GhostSearch):
  polygon_wkt = payload["polygon_wkt"]
  datetime = payload["datetime_collected"]
  future = payload["future"]

  return get_annotation_ghosts_by_geometry(polygon_wkt, datetime, future)


class GhostResult(TypedDict):
  image_id: str
  datetime: int
  annotations: list[dict]


def get_annotation_ghosts_by_geometry(
  polygon_wkt: str, datetime: int, future: bool
) -> list[GhostResult]:
  data: dict[str, GhostResult] = {}

  def map_row(row: Row):
    r = dict(row)

    label = "\n".join(
      [
        r["equipment_label"],
        r["confidence_label"],
        r["status_label"],
      ]
    )

    image_id = encode_sha256_to_b64(r["image"])

    ghost_result = data.setdefault(
      image_id,
      GhostResult(image_id=image_id, datetime=r["datetime"], annotations=[]),
    )

    ghost_result["annotations"].append(
      {
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
      }
    )

  def build_subquery(geometry: EquipmentGeometry):
    return (
      SelectQuery()
      .select(
        "ea.id AS id",
        "ea.image AS image",
        "i.images.datetime_collected AS datetime",
        "AsGeoJSON(ea.geometry) AS geometry",
        "ea.equipment AS equipment_id",
        "ed.equipment.displayName AS equipment_label",
        "ea.confidence AS confidence_id",
        "a.observation_confidence.name AS confidence_label",
        "ea.status AS status_id",
        "a.equipment_status.name AS status_label",
      )
      .from_(f"equipment_{geometry.lower()} ea")
      .inner_join("i.images", "i.images.id = ea.image")
      .inner_join("ed.equipment", "ed.equipment.id = ea.equipment")
      .inner_join(
        "a.observation_confidence", "a.observation_confidence.id = ea.confidence"
      )
      .inner_join("a.equipment_status", "a.equipment_status.id = ea.status")
      .cross_join("poly")
      .where(f"i.images.datetime_collected {date_op} ?", datetime)
      .where("ST_Intersects(ea.geometry, poly.geom)")
    )

  date_op = ">" if future else "<"

  attach_sql = (
    f"ATTACH DATABASE '{app_settings.INDEX_DB}' AS i",
    f"ATTACH DATABASE '{app_settings.EQUIPMENT_DB}' AS ed",
    f"ATTACH DATABASE '{app_settings.ATTRIBUTE_DB}' AS a",
  )
  detach_sql = ("DETACH i", "DETACH DATABASE ed", "DETACH DATABASE a")

  polygon_cte = (
    SelectQuery()
    .select("geom", "ST_Area(geom) AS area")
    .from_("(SELECT ST_GeomFromText(?, 4326) AS geom) AS tmp", polygon_wkt)
  )

  geometries = ["POINT", "POLYGON"]
  subqueries = [build_subquery(g) for g in geometries]
  select_sql, params = UnionQuery(*subqueries, cte=polygon_cte, cte_name="poly").build()

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    db.conn.row_factory = Row
    cursor = db.conn.cursor()

    for statement in attach_sql:
      cursor.execute(statement)

    try:
      for r in cursor.execute(select_sql, params):
        map_row(r)

      return sorted(data.values(), key=lambda d: d["datetime"])

    finally:
      for statement in detach_sql:
        cursor.execute(statement)


class AnnotationConvert(TypedDict):
  id: str
  geometry: str
  modifiedByUserId: str
  modifiedAtTimestamp: str


def convert_annotation(payload: AnnotationConvert):
  insert_sql = """
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
      :modifiedByUserId,
      createdAtTimestamp,
      :modifiedAtTimestamp,
      ST_GeomFromText(:geometry, 4326)
    FROM equipment_point
    WHERE id = :id;
  """

  delete_query = DeleteQuery().from_("equipment_point").where("id = ?", payload["id"])
  delete_sql, delete_params = delete_query.build()

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    cursor = db.conn.cursor()
    cursor.execute(insert_sql, payload)
    cursor.execute(delete_sql, delete_params)
