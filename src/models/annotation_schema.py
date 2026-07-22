import json
import uuid
from typing import Optional, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
from src.sqlite.table import Field, Table, uuid_field

app_settings = get_settings()


class AnnotationSchemaTable(Table):
  _table_name = "schema"
  id = uuid_field(True, False)
  name = Field(str, unique=True, nullable=False)
  description = Field(str)
  ordering = Field(int, nullable=False)


def create_schema_table():
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.create_table(AnnotationSchemaTable)


def get_schema_data():
  query = (
    SelectQuery()
    .select(*AnnotationSchemaTable.column_names())
    .from_(AnnotationSchemaTable.table_name())
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_model_records(AnnotationSchemaTable, query, to_json=True)


def get_schema_options():
  query = (
    SelectQuery()
    .select(
      "name AS label",
      "uuid_blob_to_str(id) AS value",
    )
    .from_(AnnotationSchemaTable.table_name())
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_model_records(AnnotationSchemaTable, query)


def get_schema_data_options():
  query = (
    SelectQuery()
    .select(
      "name AS label",
      "json_object('id', uuid_blob_to_str(id), 'name', name) AS value",
    )
    .from_(AnnotationSchemaTable.table_name())
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_model_records(AnnotationSchemaTable, query)

  return [{**r, "value": json.loads(r["value"])} for r in records]


def get_next_ordering() -> int:
  query = (
    SelectQuery()
    .select("COALESCE(MAX(ordering) + 1, 0) AS ordering")
    .from_(AnnotationSchemaTable.table_name())
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(query)

  return int(records[0]["ordering"])


class InsertSchema(TypedDict):
  name: str
  description: Optional[str]
  ordering: Optional[int]


def insert_schema(payload: InsertSchema):
  new_id = uuid.uuid4()
  description = payload.get("description")
  ordering = payload.get("ordering")

  if ordering is None:
    ordering = get_next_ordering()

  record = {
    "id": new_id,
    "name": payload["name"],
    "description": description,
    "ordering": ordering,
  }

  table_row = AnnotationSchemaTable.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "name": payload["name"],
    "description": description,
    "ordering": ordering,
  }


class UpdateSchema(TypedDict):
  id: str
  name: str
  description: str
  ordering: Optional[int]


def update_schema(payload: UpdateSchema):
  update_id = uuid.UUID(payload["id"])
  ordering = payload.get("ordering")

  if ordering is None:
    ordering = get_next_ordering()

  update_fields = {
    "id": update_id,
    "name": payload["name"],
    "description": payload["description"],
    "ordering": ordering,
  }

  table_row = AnnotationSchemaTable.from_dict(update_fields)

  update_query = UpdateQuery().set_excluded("name", "description")

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], "id", update_query)

  return {
    "id": payload["id"],
    "name": payload["name"],
    "description": payload["description"],
    "ordering": ordering,
  }
