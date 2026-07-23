import json
import uuid
from collections import defaultdict
from typing import Optional, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
from src.sqlite.table import (
  Field,
  Index,
  Table,
  uuid_field,
)

app_settings = get_settings()

ATTRIBUTE_TABLES = (
  "activity_categories",
  "activity_likelihood",
  "observation_confidence",
  "equipment_status",
  "equipment_configuration",
  "equipment_modification",
  "equipment_visibility",
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
    name = Field(str, nullable=False)
    description = Field(str)
    ordering = Field(int, nullable=False)

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


def attribute_index_name(table: str) -> str:
  return f"ix_{table}_schema_name"


def get_attribute_tables():
  query = SelectQuery().select("name", "label").from_(AttributeTableList.table_name())

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_model_records(AttributeTableList, query)


def validate_attribute_table(table: str):
  if table not in ATTRIBUTE_TABLES:
    raise ValueError(f"Invalid attribute table: {table}")


class AttributeOption(TypedDict):
  label: str
  value: str


def get_attribute_options(table: str):
  validate_attribute_table(table)
  model = make_attribute_model(table)

  query = (
    SelectQuery()
    .select("name AS label", "uuid_blob_to_str(id) AS value")
    .from_(table)
    .order_by("ordering")
  )

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_model_records(model, query, True)


def make_attribute_query(table: str):
  return (
    SelectQuery()
    .select(
      "uuid_blob_to_str(a.id) AS id",
      "json_object('id', uuid_blob_to_str(a.schema), 'name', s.name) as schema",
      "a.name AS name",
      "a.description AS description",
      "a.ordering AS ordering",
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

  query = (
    SelectQuery()
    .select("uuid_blob_to_str(a.id) AS id", "name", "description", "ordering")
    .from_(table)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(query)


def get_next_ordering(table: str) -> int:
  query = (
    SelectQuery().select("COALESCE(MAX(ordering) + 1, 0) AS ordering").from_(table)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(query)

  return int(records[0]["ordering"])


class AttributeInsert(TypedDict):
  name: str
  description: Optional[str]
  ordering: Optional[int]


def insert_attribute(table_name: str, payload: AttributeInsert):
  validate_attribute_table(table_name)
  table_model = make_attribute_model(table_name)

  new_id = uuid.uuid4()
  description = payload.get("description")
  ordering = payload.get("ordering")

  if ordering is None:
    ordering = get_next_ordering(table_name)

  record = {
    "id": new_id,
    "name": payload["name"],
    "description": description,
    "ordering": ordering,
  }

  table_row = table_model.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "name": payload["name"],
    "description": description,
    "ordering": ordering,
  }


class AttributeUpdate(TypedDict):
  id: str
  name: str
  description: Optional[str]
  ordering: Optional[int]


def update_attribute(table_name: str, payload: AttributeUpdate):
  validate_attribute_table(table_name)
  table_model = make_attribute_model(table_name)

  update_id = uuid.UUID(payload["id"])
  ordering = payload.get("ordering")

  if ordering is None:
    ordering = get_next_ordering(table_name)

  update_fields = {
    "id": update_id,
    "name": payload["name"],
    "description": payload["description"],
    "ordering": ordering,
  }

  table_row = table_model.from_dict(update_fields)

  update_query = UpdateQuery().set_excluded("name", "description", "ordering")

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], "id", update_query)

  return {
    "id": payload["id"],
    "name": payload["name"],
    "description": payload["description"],
    "ordering": ordering,
  }
