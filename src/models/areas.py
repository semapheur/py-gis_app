import uuid
from typing import Optional, TypedDict

from src.const import LOCATION_DB
from src.spatialite import (
  Field,
  Model,
  OnConflict,
  SqliteDatabase,
  datetime_field,
  uuid_field,
)


class AreasTable(Model):
  _table_name = "areas"
  id = uuid_field(True)
  name = Field(str, nullable=False)
  description = Field(str)
  geometry = Field(str, geometry_type="POLYGON")
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


def create_areas_tables():
  with SqliteDatabase(LOCATION_DB, spatial=True) as db:
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

  with SqliteDatabase(LOCATION_DB, spatial=True) as db:
    where = "areas.name = :name AND areas.id != :id"
    params = {"name": payload["name"], "id": uuid.UUID(payload["id"]).bytes}
    found_name = db.select_records(
      AreasTable,
      columns=("name",),
      where=where,
      params=params,
    )

    if found_name:
      return found_name

    model = AreasTable.from_dict(payload, json=True)
    db.insert_models((model,), on_conflict=on_conflict)
