import json
import uuid
from typing import TypedDict

from src.const import ATTRIBUTE_DB
from src.spatialite import (
  UUID_FIELD,
  Field,
  JoinClause,
  Model,
  OnConflict,
  SqliteDatabase,
  SqliteValue,
  datetime_field,
)

BASE_ATTRIBUTE_TABLES = (
  "activity_categories",
  "equipment_status",
  "observation_confidence",
  "activity_likelihood",
  "classification",
  "releasability",
)

FTS_COLUMNS = (
  "displayName",
  "description",
  "descriptionShort",
  "natoName",
  "nativeName",
  "alternativeNames",
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
  {"id": "description", "header": "Description", "editor": "textarea"},
  {"id": "descriptionShort", "header": "Description (short)", "editor": "text"},
  {"id": "natoName", "header": "NATO name", "editor": "text"},
  {"id": "nativeName", "header": "Native name", "editor": "text"},
  {"id": "alternativeNames", "header": "Alternative names", "editor": "text"},
  {"id": "source", "header": "Source", "editor": "text"},
  {"id": "sourceData", "header": "Source data", "editor": "textarea"},
]

BASE_ATTRIBUTE_COLUMNS = [
  {"id": "text", "header": "Text", "editor": "text"},
  {"id": "description", "header": "Description", "editor": "textarea"},
]


class DataGridSchemaTable(Model):
  _table_name = "datagrid_schema"

  table_name = Field(str, primary_key=True)
  label = Field(str, nullable=False)
  columns = Field(
    str,
    nullable=False,
    to_sql=lambda x: json.dumps(x),
    from_sql=lambda x: json.loads(x),
  )


class EquipmentListTable(Model):
  _table_name = "equipment"
  id = UUID_FIELD
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
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


def make_attribute_table(table_name: str) -> type[Model]:
  class AttributeTable(Model):
    _table_name = table_name

    id = UUID_FIELD
    text = Field(str, nullable=False, unique=True)
    description = Field(str)
    createdByUserId = Field(str)
    modifiedByUserId = Field(str)
    createdAtTimestamp = datetime_field(False)
    modifiedAtTimestamp = datetime_field(True)

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
    db.create_fts_table(EquipmentListTable, FTS_COLUMNS)

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


def get_attribute_tables():
  with SqliteDatabase(ATTRIBUTE_DB) as db:
    records = db.select_records(DataGridSchemaTable, columns=("table_name", "label"))
    return records


def validate_attribute_table(table: str):
  if table not in ATTRIBUTE_TABLES:
    raise ValueError(f"Invalid attribute table: {table}")


def get_attribute_data(table: str, options: bool = False):
  validate_attribute_table(table)

  if table == "equipment":
    model = EquipmentListTable

  elif table in BASE_ATTRIBUTE_TABLES:
    model = make_attribute_table(table)

  else:
    raise ValueError(f"Invalid table name: {table}")

  with SqliteDatabase(ATTRIBUTE_DB) as db:
    if options:
      derived_columns = {"label": "text", "value": "id"}
      result = db.select_records(model, derived=derived_columns, to_json=True)
      for option in result:
        option["value"] = str(uuid.UUID(bytes=option["value"]))

      return result

    return db.select_records(model, "*", to_json=True)


def get_attribute_schema(table: str):
  validate_attribute_table(table)

  with SqliteDatabase(ATTRIBUTE_DB) as db:
    where = "table_name = :table"
    params = {"table": table}
    records = db.select_records(
      DataGridSchemaTable,
      columns=("columns",),
      where=where,
      params=params,
    )

  return records[0]


class AttributeUpdate(TypedDict):
  upsert: list[dict[str, SqliteValue]]
  delete: list[str]


def update_attributes(table: str, payload: AttributeUpdate):
  validate_attribute_table(table)

  if table == "equipment":
    model = EquipmentListTable
    update_sql = """UPDATE SET
      identifier = excluded.identifier,
      displayName = excluded.displayName,
      description = excluded.description,
      descriptionShort = excluded.descriptionShort,
      natoName = excluded.natoName,
      nativeName = excluded.nativeName,
      alternativeNames = excluded.alternativeNames
      source = excluded.source,
      sourceData = excluded.sourceData,
      modifiedByUserId = excluded.modifiedByUserId,
      modifiedAtTimestamp = excluded.modifiedAtTimestamp
    """

  elif table in BASE_ATTRIBUTE_TABLES:
    model = make_attribute_table(table)
    update_sql = """UPDATE SET
      text = excluded.text,
      description = excluded.description,
      modifiedByUserId = excluded.modifiedByUserId,
      modifiedAtTimestamp = excluded.modifiedAtTimestamp
    """

  else:
    raise ValueError(f"Invalid table name: {table}")

  upsert_models = [model.from_dict(record, json=True) for record in payload["upsert"]]
  delete_ids = [uuid.UUID(u) for u in payload["delete"]]

  with SqliteDatabase(ATTRIBUTE_DB) as db:
    if upsert_models:
      on_conflict = OnConflict(index="id", action=update_sql)
      db.insert_models(upsert_models, on_conflict)

    if delete_ids:
      db.delete_by_ids(model, delete_ids)


def search_equipment(query: str):
  columns = ("id", "displayName")
  where = "equipment_fts MATCH :query"
  params = {"query": query}
  join = JoinClause(
    join_type="LEFT", expression="equipment_fts ON equipment.id = equipment_fts.rowid"
  )

  with SqliteDatabase(ATTRIBUTE_DB) as db:
    return db.select_records(
      EquipmentListTable,
      columns=columns,
      join=join,
      where=where,
      params=params,
    )
