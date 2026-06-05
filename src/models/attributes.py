import uuid
from datetime import datetime as dt
from datetime import timezone
from getpass import getuser
from typing import TypedDict

from src.bootstrap import get_settings
from src.models.update import TableUpdate, update_table
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import OnConflict, Query
from src.sqlite.table import (
  Field,
  Table,
  datetime_field,
  uuid_field,
)
from src.timeutils import datetime_to_unix

app_settings = get_settings()

ATTRIBUTE_TABLES = (
  "activity_categories",
  "equipment_status",
  "observation_confidence",
  "activity_likelihood",
  "classification",
  "releasability",
)


class TableInfo(TypedDict):
  name: str
  label: str


class AttributeTableList(Table):
  _table_name = "table_list"
  name = Field(str, primary_key=True)
  label = Field(str, nullable=False, unique=True)


def make_attribute_model(table_name: str) -> type[Table]:
  class AttributeTable(Table):
    _table_name = table_name

    id = uuid_field(True, False)
    schema = uuid_field(False, False)
    text = Field(str, nullable=False, unique=True)
    description = Field(str)
    created_by_user = Field(str, nullable=False)
    modified_by_user = Field(str)
    created_at_timestamp = datetime_field(False)
    modified_at_timestamp = datetime_field(True)

  AttributeTable.__name__ = f"{table_name.title().replace('_', '')}Table"
  return AttributeTable


def create_attribute_tables():
  table_list: list[AttributeTableList] = []
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    for table in ATTRIBUTE_TABLES:
      model = make_attribute_model(table)
      is_created = db.create_table(model)

      if is_created:
        row = {"name": table, "label": table.capitalize().replace("_", " ")}
        table_list.append(AttributeTableList.from_dict(row))

    if table_list:
      db.create_table(AttributeTableList)
      db.insert_models(table_list)


def get_attribute_tables():
  query = Query().select("name", "label").from_(AttributeTableList._table_name)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(AttributeTableList, query)


def validate_attribute_table(table: str):
  if table not in ATTRIBUTE_TABLES:
    raise ValueError(f"Invalid attribute table: {table}")


def get_attribute_options(table: str):
  validate_attribute_table(table)
  model = make_attribute_model(table)

  query = Query().select("text AS label", "id AS value").from_(table)
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    result = db.select_records(model, query, True)

    for option in result:
      option["value"] = str(uuid.UUID(bytes=option["value"]))

  return result


def make_attribute_query(table: str):
  return (
    Query()
    .select(
      "a.id AS id",
      "a.schema AS schema",
      "s.name AS schema_name",
      "a.text AS text",
      "a.description AS description",
      "a.created_by_user AS created_by_user",
      "a.created_at_timestamp AS created_at_timestamp",
      "a.modified_by_user AS modified_by_user",
      "a.modified_at_timestamp AS modified_at_timestamp",
    )
    .from_(f"{table} a")
    .join(
      "schema s",
      on="a.schema = s.id",
      join_type="LEFT",
    )
  )


def get_attribute_data(table: str):
  validate_attribute_table(table)
  model = make_attribute_model(table)

  query = make_attribute_query(table)
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(model, query)

  return [
    {
      "schema": {"value": str(r["schema"]), "label": r["schema_name"]},
      **{k: v for k, v in r.items() if k not in ("schema", "schema_name")},
    }
    for r in records
  ]


class SchemaValue(TypedDict):
  value: str
  label: str


class InsertAttribute(TypedDict):
  schema: SchemaValue
  text: str
  description: str


def insert_attribute(table_name: str, payload: InsertAttribute):
  validate_attribute_table(table_name)
  table_model = make_attribute_model(table_name)

  new_id = uuid.uuid4()
  username = getuser()
  created_timestamp = datetime_to_unix(dt.now(timezone.utc))

  record = {
    "id": new_id,
    "schema": uuid.UUID(payload["schema"]["value"]),
    "text": payload["text"],
    "description": payload["description"],
    "created_by_user_id": username,
    "created_at_timestamp": created_timestamp,
    "modified_by_user_id": None,
    "modified_at_timestamp": None,
  }

  table_row = table_model.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  record["id"] = str(new_id)
  record["schema"] = payload["schema"]

  return record


class UpdateAttribute(TypedDict):
  id: str
  schema: SchemaValue
  text: str
  description: str


def update_attribute(table_name: str, payload: UpdateAttribute):
  validate_attribute_table(table_name)
  table_model = make_attribute_model(table_name)

  username = getuser()
  modified_timestamp = datetime_to_unix(dt.now(timezone.utc))

  update_id = uuid.UUID(payload["id"])

  update_fields = {
    "id": update_id,
    "schema": uuid.UUID(payload["schema"]["value"]),
    "text": payload["text"],
    "description": payload["description"],
    "modified_by_user": username,
    "modified_at_timestamp": modified_timestamp,
  }

  table_row = table_model.from_dict(update_fields)

  update_sql = """UPDATE SET
    schema = excluded.schema,
    text = excluded.text,
    description = excluded.description,
    modified_by_user = excluded.modified_by_user,
    modified_at_timestamp = excluded.modified_at_timestamp
  """
  on_conflict = OnConflict(index="id", action=update_sql)

  query = (
    Query()
    .select("created_by_user", "created_at_timestamp")
    .from_(table_name)
    .where("id = ?", update_id.bytes)
  )

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], on_conflict)
    rest_record = db.select_records(table_model, query)[0]

  return {
    "id": str(update_id),
    "schema": payload["schema"],
    "text": payload["text"],
    "description": payload["description"],
    "modified_by_user": username,
    "modified_at_timestamp": modified_timestamp,
    **rest_record,
  }


def update_attributes(table: str, payload: TableUpdate):
  validate_attribute_table(table)

  model = make_attribute_model(table)
  update_sql = """UPDATE SET
    text = excluded.text,
    description = excluded.description,
    modifiedByUserId = excluded.modifiedByUserId,
    modifiedAtTimestamp = excluded.modifiedAtTimestamp
  """

  return update_table(app_settings.ATTRIBUTE_DB, model, payload, update_sql)
