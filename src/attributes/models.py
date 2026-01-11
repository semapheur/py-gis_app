from src.const import ATTRIBUTE_DB
from src.spatialite import DATETIME_FIELD, Field, Model, SqliteDatabase


class ActivityListTable(Model):
  table_name = "activity"
  id = Field(str, primary_key=True)
  text = Field(str, nullable=False, unique=True)
  description = Field(str)


class EquipmentListTable(Model):
  table_name = "equipment"
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


EQUIPMENT_DATAGRID_COLUMNS = [
  {"id": "id", "header": "ID"},
  {"id": "identifier", "header": "Identifier", "editor": "text"},
  {"id": "displayName", "header": "Display name", "editor": "text"},
  {"id": "description", "header": "Description", "editor": "text"},
  {"id": "descriptionShort", "header": "Description (short)", "editor": "text"},
  {"id": "natoName", "header": "NATO name", "editor": "text"},
  {"id": "nativeName", "header": "Native name", "editor": "text"},
  {"id": "alternativeNames", "header": "Alternative names", "editor": "text"},
  {"id": "source", "header": "Source", "editor": "text"},
  {"id": "sourceData", "header": "Source data", "editor": "text"},
  {"id": "createdByUserId", "header": "Created by"},
  {"id": "createdAtTimestamp", "header": "Modified by"},
  {"id": "modifiedByUserId", "header": "Modified by"},
  {"id": "modifiedAtTimestamp", "header": "Modified by"},
]

ACTIVITY_DATAGRID_COLUMNS = [
  {"id": "id", "header": "ID"},
  {"id": "text", "header": "Text", "editor": "text"},
  {"id": "description", "header": "Description"},
]


def create_tables():
  with SqliteDatabase(ATTRIBUTE_DB) as db:
    db.create_table(ActivityListTable)
    db.create_table(EquipmentListTable)
