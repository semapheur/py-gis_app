import uuid
from typing import Literal, Optional, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery, build_junction_array_sql
from src.sqlite.table import (
  Field,
  Table,
  uuid_field,
  uuid_list_junction_model,
)
from src.sqlite.validator import min_value, one_of

SECURITY_TABLES = ("classification", "partner", "keyword")

app_settings = get_settings()


class ClassificationTable(Table):
  _table_name = "classification"

  id = uuid_field(True, False)
  name = Field(str, nullable=False)
  short_name = Field(str, nullable=False)
  level = Field(int, unique=True, nullable=False, validators=[min_value(0)])
  ordering = Field(int, nullable=False)


class KeywordTable(Table):
  _table_name = "keyword"

  id = uuid_field(True, False)
  name = Field(str, nullable=False)
  short_name = Field(str, nullable=False)
  ordering = Field(int, nullable=False)


class PartnerTable(Table):
  _table_name = "partner"

  id = uuid_field(True, False)
  name = Field(str, nullable=False)
  short_name = Field(str, nullable=False)
  type = Field(str, nullable=False, validators=[one_of("country", "group")])


member_junction = uuid_list_junction_model(PartnerTable, "members")


def create_security_tables():
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.create_table(ClassificationTable)
    db.create_table(KeywordTable)
    db.create_table(PartnerTable)
    db.create_table(member_junction)
    db.create_table_indexes(member_junction)


def get_security_attribute_tables():
  return [{"name": t, "label": t.capitalize()} for t in SECURITY_TABLES]


def validate_security_table(table: str):
  if table not in SECURITY_TABLES:
    raise ValueError(f"Invalid attribute table: {table}")


def select_security_query(table: str):
  if table == "classification":
    return (
      SelectQuery()
      .select("uuid_blob_to_str(id) AS id", "name", "short_name", "level", "ordering")
      .from_("classification")
    )

  if table == "keyword":
    return (
      SelectQuery()
      .select("uuid_blob_to_str(id) AS id", "name", "short_name", "ordering")
      .from_("keyword")
    )

  if table == "partner":
    array_sql = build_junction_array_sql(
      "partner_members", "partner", "name", "partner"
    )
    return (
      SelectQuery()
      .select(
        "uuid_blob_to_str(id) AS id",
        "name",
        "short_name",
        "type",
        f"({array_sql}) AS members",
      )
      .from_("partner")
    )

  raise ValueError(f"Invalid security table: {table}")


def get_security_data(table: str):
  validate_security_table(table)
  query = select_security_query(table)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(query)


def get_next_ordering(table: str) -> int:
  query = (
    SelectQuery().select("COALESCE(MAX(ordering) + 1, 0) AS ordering").from_(table)
  )
  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    records = db.select_records(query)

  return int(records[0]["ordering"])


class SecurityInsert(TypedDict):
  name: str
  level: int
  ordering: Optional[int]


def insert_sequrity(table_name: str, payload: SecurityInsert):
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
    "ordering": ordering,
  }

  table_row = table_model.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "name": payload["name"],
    "level": payload["level"],
    "ordering": ordering,
  }


class PartnerInsert(TypedDict):
  id: str
  name: str
  short_name: str
  type: Literal["country", "group"]
  members: list[str]


def insert_partner(payload: PartnerInsert):
  new_id = uuid.uuid4()

  record = {
    "id": new_id,
    "name": payload["name"],
    "short_name": payload["short_name"],
    "type": payload["type"],
    "members": payload["members"],
  }

  table_row = PartnerTable.from_dict(record)

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "name": payload["name"],
    "short_name": payload["short_name"],
    "type": payload["type"],
    "members": payload["members"],
  }


class SecurityUpdate(TypedDict):
  id: str
  name: str
  level: int
  ordering: Optional[int]


def update_security(table_name: str, payload: SecurityUpdate):
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
    "ordering": ordering,
  }

  table_row = table_model.from_dict(update_fields)

  update_query = UpdateQuery().set_excluded("name", "level", "ordering")

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    db.insert_models([table_row], "id", update_query)

  return {
    "id": update_id,
    "name": payload["name"],
    "level": payload["level"],
    "ordering": ordering,
  }


def search_partner(search_query: str):
  query = (
    SelectQuery()
    .select("p.id AS value", "p.name AS label")
    .from_(f"{PartnerTable.table_name()} p")
    .where(" LIKE ?", f'"%{search_query}%"')
  )

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_model_records(PartnerTable, query, True)
