import uuid
from typing import Optional, TypedDict

from src.bootstrap import get_settings
from src.models.update import TableUpdate, update_table
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import OnConflict, SelectQuery, UpdateQuery
from src.sqlite.table import (
  Field,
  Table,
  uuid_field,
)

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
    name = Field(str, nullable=False, unique=True)
    description = Field(str)

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
  query = SelectQuery().select("name", "label").from_(AttributeTableList._table_name)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(AttributeTableList, query)


def validate_attribute_table(table: str):
  if table not in ATTRIBUTE_TABLES:
    raise ValueError(f"Invalid attribute table: {table}")


def get_attribute_options(table: str):
  validate_attribute_table(table)
  model = make_attribute_model(table)

  query = (
    SelectQuery().select("name AS label", "uuid_blob_to_str(id) AS value").from_(table)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(model, query)


def make_attribute_query(table: str):
  return (
    SelectQuery()
    .select(
      "a.id AS id",
      "json_object('value', uuid_blob_to_str(a.schema), 'label', s.name) as schema",
      "a.name AS name",
      "a.description AS description",
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
    return db.select_records(model, query)

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
  name: str
  description: Optional[str]


def insert_attribute(table_name: str, payload: InsertAttribute):
  validate_attribute_table(table_name)
  table_model = make_attribute_model(table_name)

  new_id = uuid.uuid4()
  attribute_description = payload.get("description")
  schema_id = uuid.UUID(payload["schema"]["value"])
  record = {
    "id": new_id,
    "schema": schema_id,
    "name": payload["name"],
    "description": attribute_description,
  }

  table_row = table_model.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": new_id,
    "schema": payload["schema"],
    "name": payload["name"],
    "description": attribute_description,
  }


class UpdateAttribute(TypedDict):
  id: str
  schema: SchemaValue
  name: str
  description: str


def update_attribute(table_name: str, payload: UpdateAttribute):
  validate_attribute_table(table_name)
  table_model = make_attribute_model(table_name)

  update_id = uuid.UUID(payload["id"])

  update_fields = {
    "id": update_id,
    "schema": uuid.UUID(payload["schema"]["value"]),
    "name": payload["name"],
    "description": payload["description"],
  }

  table_row = table_model.from_dict(update_fields)

  update_query = (
    UpdateQuery()
    .set_raw("schema = excluded.schema")
    .set_raw("name = excluded.name")
    .set_raw("description = excluded.description")
  )

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], "id", update_query)


def update_attributes(table: str, payload: TableUpdate):
  validate_attribute_table(table)

  model = make_attribute_model(table)
  update_sql = """UPDATE SET
    name = excluded.name,
    description = excluded.description,
  """

  return update_table(app_settings.ATTRIBUTE_DB, model, payload, update_sql)
