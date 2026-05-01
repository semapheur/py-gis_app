from src.bootstrap import get_settings
from src.models.update import TableUpdate, update_table
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import Query
from src.sqlite.table import Field, Table, datetime_field, uuid_field

app_settings = get_settings()

FTS_COLUMNS = (
  "displayName",
  "description",
  "descriptionShort",
  "natoName",
  "nativeName",
  "alternativeNames",
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
  createdByUserId = Field(str)
  modifiedByUserId = Field(str)
  createdAtTimestamp = datetime_field(False)
  modifiedAtTimestamp = datetime_field(True)


class EquipmentSearch(Table):
  _table_name = "equipment_fts"
  value = uuid_field(True, False)
  label = Field(str, nullable=False)


def create_equipment_table():
  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    db.create_table(EquipmentList)
    db.create_fts_table(EquipmentList, FTS_COLUMNS)


def search_equipment(search_query: str):
  query = (
    Query()
    .select("e.id AS value", "e.displayName AS label")
    .from_(EquipmentSearch._table_name)
    .inner_join("equipment e", "e.rowid = equipment_fts.rowid")
    .where("equipment_fts MATCH ?", f'"{search_query}"')
  )

  with SqliteDatabase(app_settings.ATTRIBUTE_DB) as db:
    return db.select_records(EquipmentSearch, query, True)


def update_equipment(payload: TableUpdate):

  update_sql = """UPDATE SET
    identifier = excluded.identifier,
    displayName = excluded.displayName,
    description = excluded.description,
    descriptionShort = excluded.descriptionShort,
    natoName = excluded.natoName,
    nativeName = excluded.nativeName,
    alternativeNames = excluded.alternativeNames,
    source = excluded.source,
    sourceData = excluded.sourceData,
    modifiedByUserId = excluded.modifiedByUserId,
    modifiedAtTimestamp = excluded.modifiedAtTimestamp
  """

  return update_table(app_settings.EQUIPMENT_DB, EquipmentList, payload, update_sql)
