import re
import uuid
from typing import Literal, TypedDict, Union

from src.bootstrap import get_settings
from src.models.equipment_annotation import (
  MULTI_ATTRIBUTE_FIELDS,
  SINGLE_ATTRIBUTE_FIELDS,
  AnnotationModels,
  create_equipment_annotation_tables,
  equipment_annotation_models,
  get_equipment_annotations_by_image,
)
from src.models.personnel_annotation import (
  PERSONNEL_MODELS,
  PERSONNEL_UPDATE_FIELDS,
  create_personnel_annotation_tables,
  get_personnel_annotations_by_image,
)
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import UpdateQuery
from src.sqlite.table import Table

type AnnotationType = Literal["activity", "equipment", "personnel"]

ANNOTATION_TYPES = ("activity", "equipment", "personnel")


app_settings = get_settings()


class AnnotationUpdate(TypedDict):
  type: AnnotationType
  data: dict[str, Union[int, str, None]]


def create_annotation_tables():
  create_equipment_annotation_tables()
  create_personnel_annotation_tables()


def update_annotations(payloads: list[AnnotationUpdate]):
  wkt_pattern = re.compile(
    r"^(?:SRID=\d+;)?(POINT|POLYGON|MULTIPOLYGON)", re.IGNORECASE
  )

  equipment_rows: list[Table] = []
  personnel_rows: dict[str, list[Table]] = {"POINT": [], "POLYGON": []}
  list_writes: list[tuple[AnnotationModels, uuid.UUID, dict[str, list[uuid.UUID]]]] = []

  equipment_update_query = UpdateQuery().set_excluded(
    "geometry",
    "equipment",
    *SINGLE_ATTRIBUTE_FIELDS,
    "heading_deg",
    "speed_mps",
    "modifiedByUserId",
    "modifiedAtTimestamp",
  )

  for payload in payloads:
    annotation_type = payload.get("type")

    data = payload.get("data")
    if data is None:
      raise ValueError("Missing annotation data")

    geometry_wkt = data.get("geometry", "")
    match = wkt_pattern.search(geometry_wkt)
    if match is None:
      raise ValueError(f"Invalid WKT: {geometry_wkt}")

    geometry = match.group(1)

    if annotation_type == "equipment":
      models = equipment_annotation_models(geometry)
      equipment_rows.append(models.annotation.from_dict(data, True))

      parent_id = uuid.UUID(data["id"])
      field_ids = {
        field: [uuid.UUID(u) for u in data.get(field) or []]
        for field in MULTI_ATTRIBUTE_FIELDS
      }
      list_writes.append((models, parent_id, field_ids))

    elif annotation_type == "personnel":
      print(payload)
      if geometry not in personnel_rows:
        raise ValueError(f"Unsupported personnel geometry: {geometry}")

      personnel_rows[geometry].append(PERSONNEL_MODELS[geometry].from_dict(data, True))

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    if equipment_rows:
      db.insert_models(equipment_rows, "id", equipment_update_query)

    for geometry, rows in personnel_rows.items():
      if not rows:
        continue

      q = UpdateQuery().set_excluded(
        *PERSONNEL_UPDATE_FIELDS[geometry], "modifiedByUserId", "modifiedAtTimestamp"
      )
      db.insert_models(rows, "id", q)

    for models, parent_id, field_ids in list_writes:
      for field, ids in field_ids.items():
        db.set_uuid_list(models.junctions[field], parent_id, ids)


def delete_annotations(payload: dict[str, list[str]]):
  supported_keys = {
    "activity": {"multipolygon"},
    "equipment": {"point", "polygon"},
    "personnel": {"point", "polygon"},
  }

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
      return equipment_annotation_models(geometry).annotation

    if annotation_type == "personnel":
      return PERSONNEL_MODELS[geometry.upper()]

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
  return {
    "equipment": get_equipment_annotations_by_image(image_id),
    "personnel": get_personnel_annotations_by_image(image_id),
  }
