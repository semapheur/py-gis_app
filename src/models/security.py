import uuid
from typing import Optional, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
from src.sqlite.table import (
  Field,
  Table,
  uuid_field,
)

SECURITY_TABLES = (
  "classification",
  "releasability"
)

app_settings = get_settings()

def make_security_model(table_name: str) -> type[Table]:
  class SecurityTable(Table):
    _table_name = table_name

    id = uuid_field(True, False)
    name = Field(str, nullable=False)
    level = Field(int, unique=True)
    ordering = Field(int, nullable=False)

  SecurityTable.__name__ = f"{table_name.title().replace('_', '')}Table"
  return SecurityTable

def create_security_tables():
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    for table in SECURITY_TABLES:
      model = make_security_model(table)
      db.create_table(model)

def validate_security_table(table: str):
  if table not in SECURITY_TABLES:
    raise ValueError(f"Invalid attribute table: {table}")

def get_security_data(table: str):
  validate_security_table(table)

  query = SelectQuery().select(
    "uuid_blob_to_str(a.id) AS id",
    "name",
    "level",
    "ordering"
  ).from_(f"{table} a")

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(query)

  return records

def get_next_ordering(table: str) -> int:
  query = SelectQuery().select("SELECT MAX(ordering) + 1 AS ordering").from_(table)
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(query)

  return int(records[0]["ordering"])

class InsertSecurity(TypedDict):
  name: str
  level: int
  ordering: Optional[int]


def insert_sequrity(table_name: str, payload: InsertSecurity):
  validate_security_table(table_name)
  table_model = make_security_model(table_name)

  new_id = uuid.uuid4()
  ordering = payload.get("ordering")

  if ordering is None:
    ordering = get_next_ordering(table_name)

  record = {
    "id": new_id,
    "name": payload["name"],
    "level": payload["level"],
    "ordering": ordering
  }

  table_row = table_model.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "name": payload["name"],
    "level": payload["level"],
    "ordering": ordering
  }

class UpdateSecurity(InsertSecurity):
  id: str

def update_security(table_name: str, payload: UpdateSecurity):
  validate_security_table(table_name)
  table_model = make_security_model(table_name)

  update_id = uuid.UUID(payload["id"])
  ordering = payload.get("ordering")

  if ordering is None:
    ordering = get_next_ordering(table_name)

  update_fields = {
    "id": update_id,
    "name": payload["name"],
    "level": payload["level"],
    "ordering": ordering
  }

  table_row = table_model.from_dict(update_fields)

  update_query = UpdateQuery().set_excluded("schema", "name", "description")

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], "id", update_query)

  return {
    "id": update_id,
    "name": payload["name"],
    "level": payload["level"],
    "ordering": ordering
  }
