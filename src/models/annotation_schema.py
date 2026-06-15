import uuid
from typing import TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import OnConflict, Query
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
  query = Query().select("*").from_(AnnotationSchemaTable._table_name)
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(AnnotationSchemaTable, query)


def get_schema_options():
  query = (
    Query()
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
    Query()
    .select(
      "name AS label",
      "json_object('id', uuid_blob_to_str(id), 'name', name) AS value",
    )
    .from_(AnnotationSchemaTable._table_name)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(AnnotationSchemaTable, query)


class InsertSchema(TypedDict):
  name: str
  description: str


def insert_schema(payload: InsertSchema):
  new_id = uuid.uuid4()
  print(payload)

  record = {
    "id": new_id,
    "name": payload["name"],
    "description": payload["description"],
  }

  table_row = AnnotationSchemaTable.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "name": payload["name"],
    "description": payload["description"],
  }


class UpdateSchema(TypedDict):
  id: str
  name: str
  description: str


def update_schema(payload: UpdateSchema):
  update_id = uuid.UUID(payload["id"])

  update_fields = {
    "id": update_id,
    "name": payload["name"],
    "description": payload["description"],
  }

  table_row = AnnotationSchemaTable.from_dict(update_fields)

  update_sql = """UPDATE SET
    name = excluded.name,
    description = excluded.description,
  """
  on_conflict = OnConflict(index="id", action=update_sql)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], on_conflict)

  return {
    "id": str(update_id),
    "name": payload["name"],
    "description": payload["description"],
  }
