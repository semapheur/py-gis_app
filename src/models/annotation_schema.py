import json
import uuid
from typing import Optional, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
from src.sqlite.table import Field, Table, uuid_field

app_settings = get_settings()

FTS_COLUMNS = (
  "displayName",
  "description",
  "descriptionShort",
  "natoName",
  "nativeName",
  "alternativeNames",
)


class AnnotationSchemaTable(Table):
  _table_name = "schema"
  id = uuid_field(True, False)
  name = Field(str, unique=True, nullable=False)
  description = Field(str)


def create_schema_table():
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.create_table(AnnotationSchemaTable)


def get_schema_data():
  query = (
    SelectQuery()
    .select(*AnnotationSchemaTable.column_names())
    .from_(AnnotationSchemaTable._table_name)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(AnnotationSchemaTable, query, to_json=True)


def get_schema_options():
  query = (
    SelectQuery()
    .select(
      "name AS label",
      "uuid_blob_to_str(id) AS value",
    )
    .from_(AnnotationSchemaTable._table_name)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(AnnotationSchemaTable, query)


def get_schema_data_options():
  query = (
    SelectQuery()
    .select(
      "name AS label",
      "json_object('id', uuid_blob_to_str(id), 'name', name) AS value",
    )
    .from_(AnnotationSchemaTable._table_name)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(AnnotationSchemaTable, query)

  return [{**r, "value": json.loads(r["value"])} for r in records]


class InsertSchema(TypedDict):
  name: str
  description: Optional[str]


def insert_schema(payload: InsertSchema):
  new_id = uuid.uuid4()
  schema_description = payload.get("description")
  record = {
    "id": str(new_id),
    "name": payload["name"],
    "description": schema_description,
  }

  table_row = AnnotationSchemaTable.from_dict(record, True)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return record


class UpdateSchema(TypedDict):
  id: str
  name: str
  description: str


def update_schema(payload: UpdateSchema):
  update_id = str(uuid.UUID(payload["id"]))

  update_fields = {
    "id": update_id,
    "name": payload["name"],
    "description": payload["description"],
  }

  table_row = AnnotationSchemaTable.from_dict(update_fields, True)

  update_query = UpdateQuery().set_excluded("name", "description")

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], "id", update_query)

  return update_fields
