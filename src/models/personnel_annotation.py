from bootstrap import get_settings
from sqlite.connect import SqliteDatabase
from src.sqlite.table import (
  Field,
  GeometryField,
  Table,
  datetime_field,
  hash_field,
  uuid_field,
)

app_settings = get_settings()


class PersonnelPointAnnotation(Table):
  _table_name = "personnel_point"
  id = uuid_field(True, False)
  image = hash_field(False)
  geometry = GeometryField(str, geometry_type="POINT")
  confidence = uuid_field(False, False)
  affiliation = uuid_field(False, False)
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


class PersonnelPolygonAnnotation(Table):
  _table_name = "personnel_polygon"
  id = uuid_field(True, False)
  image = hash_field(False)
  geometry = GeometryField(str, geometry_type="POLYGON")
  min_count = Field(float)
  max_count = Field(float)
  affiliation = uuid_field(False, False)
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


def create_annotation_tables():
  with SqliteDatabase(app_settings.ANNOTATION_DB, spatial=True) as db:
    _ = db.create_table(PersonnelPointAnnotation)
    _ = db.create_table(PersonnelPolygonAnnotation)
