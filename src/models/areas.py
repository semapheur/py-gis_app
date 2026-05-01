import uuid
from typing import Optional, TypedDict

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import OnConflict, Query
from src.sqlite.table import (
  Field,
  GeometryField,
  Table,
  datetime_field,
  uuid_field,
)

app_settings = get_settings()


class AreasTable(Table):
  _table_name = "areas"
  id = uuid_field(True, False)
  name = Field(str, nullable=False)
  description = Field(str)
  geometry = GeometryField(str, geometry_type="POLYGON")
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


def create_areas_tables():
  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    db.create_table(AreasTable)


class AreaUpdate(TypedDict):
  id: str
  name: str
  description: Optional[str]
  geometry: str
  createdByUserId: str
  createdAtTimestamp: int


def update_area(payload: AreaUpdate):

  update_sql = """UPDATE SET
    name = excluded.name,
    description = excluded.description,
    geometry = excluded.geometry,
    modifiedByUserId = excluded.modifiedByUserId,
    modifiedAtTimestamp = excluded.modifiedAtTimestamp
  """

  on_conflict = OnConflict(index="id", action=update_sql)

  query = (
    Query()
    .select("name")
    .from_(AreasTable._table_name)
    .where("name = ?", payload["name"])
    .where("id != ?", uuid.UUID(payload["id"]).bytes)
  )

  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    found_name = db.select_records(AreasTable, query)

    if found_name:
      return found_name

    model = AreasTable.from_dict(payload, json=True)
    db.insert_models((model,), on_conflict=on_conflict)


class AreaId(TypedDict):
  id: str


def get_area(payload: AreaId):
  query = (
    Query()
    .select("id", "name", "description", "AsGeoJSON(geometry) AS geometry")
    .from_(AreasTable._table_name)
    .where("id = ?", uuid.UUID(payload["id"]).bytes)
  )

  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    area = db.select_records(AreasTable, query, True)
    return area[0]


def get_area_wkt(area_id: str):
  query = (
    Query()
    .select("AsText(geometry) AS geometry")
    .from_(AreasTable._table_name)
    .where("id = ?", uuid.UUID(area_id).bytes)
  )

  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    area = db.select_records(AreasTable, query, True)
    return area[0]


def get_areas():
  query = (
    Query()
    .select("id", "name", "description", "AsGeoJSON(geometry) AS geometry")
    .from_(AreasTable._table_name)
  )

  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    areas = db.select_records(AreasTable, query, True)
    return areas


class AreaDelete(TypedDict):
  delete: list[str]


def delete_areas(payload: AreaDelete):
  delete_ids = [uuid.UUID(u) for u in payload["delete"]]

  with SqliteDatabase(app_settings.LOCATION_DB, spatial=True) as db:
    db.delete_by_ids(AreasTable, delete_ids)
