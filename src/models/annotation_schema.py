from src.bootstrap import get_settings
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


class AnnotationSchemaTable(Table):
  _table_name = "schema"
  id = uuid_field(True, False)
  name = Field(str, unique=True, nullable=False)
  description = Field(str)


def create_schema_table():
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    db.create_table(AnnotationSchemaTable)
