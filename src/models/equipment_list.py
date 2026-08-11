import uuid
from typing import TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
from src.sqlite.table import Field, Index, Table, uuid_field, uuid_fk_field

app_settings = get_settings()

FTS_COLUMNS = (
  "display_name",
  "description",
  "description_short",
  "nato_name",
  "native_name",
  "alternative_names",
)


class EquipmentList(Table):
  _table_name = "equipment"
  id = uuid_field(True, False)
  identifier = Field(str, nullable=False)
  display_name = Field(str, nullable=False)
  description = Field(str)
  description_short = Field(str)
  nato_name = Field(str)
  native_name = Field(str)
  alternative_names = Field(str)
  source = Field(str)
  source_data = Field(str)


junction = ("system",)


class Equipment(Table):
  _table_name = "equipment"
  id = uuid_field(True, False)
  identifier = Field(str, nullable=False)
  display_name = Field(str, nullable=False)


class Designation(Table):
  _table = "designation"
  _indexes = tuple(Index(("equipment_id", "designation"), True))
  id = uuid_field(True, True)
  equipment_id = uuid_fk_field("equipment", "id")
  designation = Field(str, nullable=False)
  designation_type = Field(str, nullable=False)
  script = Field(str, nullable=False)
  reference = uuid_field(True, False)
  classification = uuid_field(True, False)


class Dimension(Table):
  _table = "dimension"
  _indexes = tuple(Index(("equipment_id", "meters", "dimension_type"), True))
  id = uuid_field(True, True)
  equipment_id = uuid_fk_field("equipment", "id")
  meters = Field(float, nullable=False)
  dimension_type = Field(str, nullable=False)
  reference = uuid_field(True, False)
  classification = uuid_field(True, False)


class EquipmentSearch(Table):
  _table_name = "equipment_fts"
  value = uuid_field(True, False)
  label = Field(str, nullable=False)


def create_equipment_table():
  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    db.create_table(EquipmentList)
    db.create_fts_table(EquipmentList, FTS_COLUMNS)


def get_equipment():
  query = (
    SelectQuery()
    .select(*EquipmentList.column_names())
    .from_(EquipmentList.table_name())
  )

  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    return db.select_model_records(EquipmentList, query, True)


def search_equipment(search_query: str):
  query = (
    SelectQuery()
    .select("e.id AS value", "e.display_name AS label")
    .from_(EquipmentSearch.table_name())
    .inner_join("equipment e", "e.rowid = equipment_fts.rowid")
    .where("equipment_fts MATCH ?", f'"{search_query}"')
  )

  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    return db.select_model_records(EquipmentSearch, query, True)


class InsertEquipment(TypedDict):
  identifier: str
  display_name: str
  description: str
  description_short: str
  nato_name: str
  native_name: str
  alternative_names: str
  source: str
  source_data: str


def insert_equipment(payload: InsertEquipment):

  new_id = uuid.uuid4()
  nato_name = payload.get("nato_name")
  native_name = payload.get("native_name")
  alternative_names = payload.get("alternative_names")
  source = payload.get("source")
  source_data = payload.get("data")

  record = {
    "id": new_id,
    "identifier": payload["identifier"],
    "display_name": payload["display_name"],
    "description": payload["description"],
    "description_short": payload["description_short"],
    "nato_name": nato_name,
    "native_name": native_name,
    "alternative_names": alternative_names,
    "source": source,
    "source_data": source_data,
  }

  table_row = EquipmentList.from_dict(record)

  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    db.insert_models([table_row])

  return {
    "id": str(new_id),
    "identifier": payload["identifier"],
    "display_name": payload["display_name"],
    "description": payload["description"],
    "description_short": payload["description_short"],
    "nato_name": nato_name,
    "native_name": native_name,
    "alternative_names": alternative_names,
    "source": source,
    "source_data": source_data,
  }


class UpdateEquipment(InsertEquipment):
  id: str


def update_equipment(payload: UpdateEquipment):
  update_id = uuid.UUID(payload["id"])
  nato_name = payload.get("nato_name")
  native_name = payload.get("native_name")
  alternative_names = payload.get("alternative_names")
  source = payload.get("source")
  source_data = payload.get("data")

  record = {
    "id": update_id,
    "identifier": payload["identifier"],
    "display_name": payload["display_name"],
    "description": payload["description"],
    "description_short": payload["description_short"],
    "nato_name": nato_name,
    "native_name": native_name,
    "alternative_names": alternative_names,
    "source": source,
    "source_data": source_data,
  }

  table_row = EquipmentList.from_dict(record, True)

  update_query = UpdateQuery().set_excluded(
    "identifier",
    "display_name",
    "description",
    "description_short",
    "nato_name",
    "native_name",
    "alternative_names",
    "source",
    "source_data",
  )

  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    db.insert_models([table_row], "id", update_query)

  return record
