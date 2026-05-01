import uuid
from typing import TypedDict

from src.bootstrap import get_settings
from src.models.update import TableUpdate, update_table
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import Query
from src.sqlite.table import (
  Field,
  Table,
  datetime_field,
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
    text = Field(str, nullable=False, unique=True)
    description = Field(str)
    createdByUserId = Field(str)
    modifiedByUserId = Field(str)
    createdAtTimestamp = datetime_field(False)
    modifiedAtTimestamp = datetime_field(True)

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


def get_attribute_data(table: str, options: bool = False):
  validate_attribute_table(table)

  if table in ATTRIBUTE_TABLES:
    model = make_attribute_model(table)

  else:
    raise ValueError(f"Invalid table name: {table}")

  query = Query().from_(model._table_name)
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    if options:
      query = query.select("text AS label", "id AS value")

      result = db.select_records(model, query, True)
      for option in result:
        option["value"] = str(uuid.UUID(bytes=option["value"]))

      return result

    query = query.select(*model.column_sql())
    return db.select_records(model, query, True)


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
