import json

from src.const import ATTRIBUTE_DB
from src.spatialite import DATETIME_FIELD, Field, Model, SqliteDatabase

BASE_ATTRIBUTE_TABLES = (
  "activity_categories",
  "equipment_status",
  "observation_confidence",
  "activity_likelihood",
  "classification",
  "releasability",
)

ATTRIBUTE_TABLES = {"equipment", *BASE_ATTRIBUTE_TABLES}

META_COLUMNS = [
  {"id": "id", "header": "ID"},
  {"id": "createdByUserId", "header": "Created by"},
  {"id": "createdAtTimestamp", "header": "Created at"},
  {"id": "modifiedByUserId", "header": "Modified by"},
  {"id": "modifiedAtTimestamp", "header": "Modified at"},
]

EQUIPMENT_COLUMNS = [
  {"id": "identifier", "header": "Identifier", "editor": "text"},
  {"id": "displayName", "header": "Display name", "editor": "text"},
  {"id": "description", "header": "Description", "editor": "text"},
  {"id": "descriptionShort", "header": "Description (short)", "editor": "text"},
  {"id": "natoName", "header": "NATO name", "editor": "text"},
  {"id": "nativeName", "header": "Native name", "editor": "text"},
  {"id": "alternativeNames", "header": "Alternative names", "editor": "text"},
  {"id": "source", "header": "Source", "editor": "text"},
  {"id": "sourceData", "header": "Source data", "editor": "text"},
]

BASE_ATTRIBUTE_COLUMNS = [
  {"id": "text", "header": "Text", "editor": "text"},
  {"id": "description", "header": "Description", "editor": "text"},
]


class DataGridSchemaTable(Model):
  _table_name = "datagrid_schema"

  table_name = Field(str, primary_key=True)
  label = Field(str, nullable=False)
  columns = Field(
    str,
    nullable=False,
    to_sql=lambda x: json.dumps(x),
    to_python=lambda x: json.loads(x),
  )


class EquipmentListTable(Model):
  _table_name = "equipment"
  id = Field(str, primary_key=True)
  identifier = Field(str, nullable=False)
  displayName = Field(str, nullable=False)
  description = Field(str)
  descriptionShort = Field(str)
  natoName = Field(str)
  nativeName = Field(str)
  alternativeNames = Field(str)
  source = Field(str)
  sourceData = Field(str)
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = DATETIME_FIELD
  modifiedAtTimestamp = DATETIME_FIELD


def make_attribute_table(table_name: str) -> type[Model]:
  class AttributeTable(Model):
    _table_name = table_name

    id = Field(str, primary_key=True)
    text = Field(str, nullable=False, unique=True)
    description = Field(str)
    createdByUserId = Field(str)
    modifiedByUserId = Field(str)
    createdAtTimestamp = DATETIME_FIELD
    modifiedAtTimestamp = DATETIME_FIELD

  AttributeTable.__name__ = f"{table_name.title().replace('_', '')}Table"
  return AttributeTable


def schema_from_model(
  model: type[Model],
  columns: list[dict[str, str]],
  label: str | None = None,
) -> DataGridSchemaTable:
  schema = {
    "table_name": model._table_name,
    "label": label or model._table_name.replace("_", " ").capitalize(),
    "columns": columns,
  }

  return DataGridSchemaTable.from_dict(schema)


def create_attribute_tables():
  schema_data: list[DataGridSchemaTable] = []
  equipment_schema = schema_from_model(
    EquipmentListTable,
    EQUIPMENT_COLUMNS,
    "Equipment",
  )
  schema_data.append(equipment_schema)

  with SqliteDatabase(ATTRIBUTE_DB) as db:
    db.create_table(DataGridSchemaTable)
    db.create_table(EquipmentListTable)

    for table in BASE_ATTRIBUTE_TABLES:
      model = make_attribute_table(table)
      db.create_table(model)

      attribute_schema = schema_from_model(
        model,
        BASE_ATTRIBUTE_COLUMNS,
        table.capitalize().replace("_", " "),
      )
      schema_data.append(attribute_schema)

    db.insert_models(schema_data)


def get_datagrid_schemas():
  with SqliteDatabase(ATTRIBUTE_DB) as db:
    records = db.select_records(DataGridSchemaTable, "*")

  result = {}
  for record in records:
    key = record["table_name"]
    result[key] = {"label": record["label"], "columns": record["columns"]}

  return result


def save_attributes(payload):
  pass
