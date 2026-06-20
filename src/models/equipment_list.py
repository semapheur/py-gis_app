import uuid
from typing import TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
from src.sqlite.table import Field, Table, uuid_field

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
  displayName = Field(str, nullable=False)
  description = Field(str)
  descriptionShort = Field(str)
  natoName = Field(str)
  nativeName = Field(str)
  alternativeNames = Field(str)
  source = Field(str)
  sourceData = Field(str)


class EquipmentSearch(Table):
  _table_name = "equipment_fts"
  value = uuid_field(True, False)
  label = Field(str, nullable=False)


def create_equipment_table():
  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    db.create_table(EquipmentList)
    db.create_fts_table(EquipmentList, FTS_COLUMNS)


def get_equipment():
  query = SelectQuery().from_(EquipmentList._table_name)

  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    query = query.select("*")
    return db.select_records(EquipmentList, query, True)


def search_equipment(search_query: str):
  query = (
    SelectQuery()
    .select("e.id AS value", "e.displayName AS label")
    .from_(EquipmentSearch._table_name)
    .inner_join("equipment e", "e.rowid = equipment_fts.rowid")
    .where("equipment_fts MATCH ?", f'"{search_query}"')
  )

  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    return db.select_records(EquipmentSearch, query, True)


class InsertEquipment(TypedDict):
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
    "display_name": payload["display_name"],
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
    "display_name": payload["display_name"],
    "nato_name": nato_name,
    "native_name": native_name,
    "alternative_names": alternative_names,
    "source": source,
    "source_data": source_data,
  }


class UpdateEquipment(InsertEquipment):
  id: str


def update_equipment(payload: UpdateEquipment):
  update_id = payload["id"]
  nato_name = payload.get("nato_name")
  native_name = payload.get("native_name")
  alternative_names = payload.get("alternative_names")
  source = payload.get("source")
  source_data = payload.get("data")

  record = {
    "id": update_id,
    "display_name": payload["display_name"],
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
