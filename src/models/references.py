from dataclasses import dataclass

from bootstrap import get_settings
from sqlite.connect import SqliteDatabase
from sqlite.table import (
  Field,
  Table,
  datetime_field,
  uuid_field,
  uuid_list_junction_model,
)
from src.sqlite.query_builder import SelectQuery

app_settings = get_settings()


@dataclass(frozen=True)
class AttributeTableSpec:
  name: str
  label: str
  columns: tuple[str, ...]


REFERENCE_ATTRIBUTE_TABLES = {
  "discipline": "Discipline",
  "source_type": "Source type",
}


class References(Table):
  _table_name = "reference"
  id = uuid_field(True, False)
  classification = uuid_field(False, False)
  releasability = uuid_field(False, False)
  datetime_released = datetime_field(False)
  source_type = uuid_field(False, False)
  originator = uuid_field(False, False)
  discipline = uuid_field(False, False)
  title = Field(str, nullable=False)
  url = Field(str, nullable=True)


class Originator(Table):
  _table_name = "originator"
  id = uuid_field(True, False)
  name = Field(str, nullable=False)
  name_short = Field(str, nullable=True)
  country = Field(str, nullable=False)


def make_attribute_model(table_name: str) -> type[Table]:
  class AttributeTable(Table):
    _table_name = table_name
    id = uuid_field(True, False)
    name = Field(str, nullable=False)
    description = Field(str)
    ordering = Field(int, nullable=False)

  AttributeTable.__name__ = f"{table_name.title().replace('_', '')}Table"
  return AttributeTable


def create_reference_tables():
  keyword_junction = uuid_list_junction_model(References, "keyword")

  with SqliteDatabase(app_settings.REFERENCE_DB) as db:
    db.create_table(References)
    db.create_table(keyword_junction)
    db.create_table_indexes(keyword_junction)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.create_table(Originator)

    for table in REFERENCE_ATTRIBUTE_TABLES:
      model = make_attribute_model(table)
      db.create_table(model)


def get_reference_attribute_tables():
  return [
    {"name": t._table_name, "label": t._table_name.capitalize()}
    for t in (References, Originator)
  ] + [{"name": k, "label": v} for k, v in REFERENCE_ATTRIBUTE_TABLES.items()]


def validate_reference_attribute_table(table: str):
  valid_tables = (Originator._table_name,) + tuple(REFERENCE_ATTRIBUTE_TABLES)

  if table not in valid_tables:
    raise ValueError(f"Invalid attribute table: {table}")


def get_reference_attribute_data(table: str):
  validate_reference_attribute_table(table)

  columns = None
  if table == Originator._table_name:
    columns = ("name_short", "country")
  else:
    columns = ("description", "ordering")

  query = (
    SelectQuery()
    .select("uuid_blob_to_str(a.id) AS id", "name", *columns)
    .from_(f"{table} a")
  )

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(query)
