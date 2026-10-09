import json
from sqlite3 import Row

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UnionQuery
from src.sqlite.table import (
  Field,
  GeometryField,
  Table,
  datetime_field,
  hash_field,
  uuid_field,
)

app_settings = get_settings()


class PersonnelPointAnnotation(Table):
  _table_name = "personnel_point"
  id = uuid_field(True, False)
  image = hash_field(False)
  geometry = GeometryField(str, geometry_type="POINT")
  confidence = uuid_field(False, False)
  affiliation = uuid_field(False, False)
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


class PersonnelPolygonAnnotation(Table):
  _table_name = "personnel_polygon"
  id = uuid_field(True, False)
  image = hash_field(False)
  geometry = GeometryField(str, geometry_type="POLYGON")
  min_count = Field(float)
  max_count = Field(float)
  confidence = uuid_field(False, False)
  affiliation = uuid_field(False, False)
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


PERSONNEL_MODELS: dict[str, type[Table]] = {
  "POINT": PersonnelPointAnnotation,
  "POLYGON": PersonnelPolygonAnnotation,
}
PERSONNEL_UPDATE_FIELDS = {
  "POINT": ("geometry", "confidence", "affiliation"),
  "POLYGON": ("geometry", "min_count", "max_count", "confidence", "affiliation"),
}


def create_personnel_annotation_tables():
  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    _ = db.create_table(PersonnelPointAnnotation)
    _ = db.create_table(PersonnelPolygonAnnotation)


def get_personnel_annotations_by_image(image_id: bytes):
  def map_row(row: Row) -> dict:
    r = dict(row)
    return {
      "id": r["id"],
      "geometry": json.loads(r["geometry"]),
      "label": r["label"],
      "data": {
        "affiliation": {"id": r["affiliation_id"], "label": r["affiliation_label"]},
        "confidence": {"id": r["confidence_id"], "label": r["confidence_label"]},
        "min_count": r["min_count"],
        "max_count": r["max_count"],
      },
      "metaData": {
        k: r[k]
        for k in (
          "createdByUserId",
          "modifiedByUserId",
          "createdAtTimestamp",
          "modifiedAtTimestamp",
        )
      },
    }

  def build_subquery(geometry: str):
    is_point = geometry == "POINT"

    label = (
      "'Pax' || '\n' || a.equipment_confidence.name AS label"
      if is_point
      else "'Pax (' || CAST(pa.min_count AS INT)"
      " || '-' || CAST(pa.max_count AS INT) || ')' || '\n' || a.equipment_confidence.name AS label"
    )

    fields = [
      "uuid_blob_to_str(pa.id) AS id",
      "AsGeoJSON(pa.geometry) AS geometry",
      label,
      "uuid_blob_to_str(pa.affiliation) AS affiliation_id",
      "a.equipment_affiliation.name AS affiliation_label",
      "uuid_blob_to_str(pa.confidence) AS confidence_id",
      "a.equipment_confidence.name AS confidence_label",
      "NULL AS min_count" if is_point else "pa.min_count AS min_count",
      "NULL AS max_count" if is_point else "pa.max_count AS max_count",
      "pa.createdByUserId AS createdByUserId",
      "pa.modifiedByUserId AS modifiedByUserId",
      "pa.createdAtTimestamp AS createdAtTimestamp",
      "pa.modifiedAtTimestamp AS modifiedAtTimestamp",
    ]
    return (
      SelectQuery()
      .select(*fields)
      .from_(f"personnel_{geometry.lower()} pa")
      .inner_join(
        "a.equipment_affiliation", "a.equipment_affiliation.id = pa.affiliation"
      )
      .inner_join("a.equipment_confidence", "a.equipment_confidence.id = pa.confidence")
      .where("pa.image = ?", image_id)
    )

  sql, params = UnionQuery(*[build_subquery(g) for g in ("POINT", "POLYGON")]).build()

  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    db.conn.row_factory = Row
    cur = db.conn.cursor()
    cur.execute(f"ATTACH DATABASE '{app_settings.ATTRIBUTE_DB}' AS a")
    try:
      return [map_row(r) for r in cur.execute(sql, params)]
    finally:
      cur.execute("DETACH DATABASE a")
