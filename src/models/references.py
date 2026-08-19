from bootstrap import get_settings
from sqlite.connect import SqliteDatabase
from sqlite.table import Field, Table, datetime_field, uuid_field

app_settings = get_settings()


class References(Table):
  _table_name = "references"
  id = uuid_field(True, False)
  classification = uuid_field(False, False)
  releasability = uuid_field(False, False)
  datetime_released = datetime_field(False)
  source_type = Field(str, nullable=False)
  originator = Field(str, nullable=False)
  title = Field(str, nullable=False)
  url = Field(str, nullable=True)


def create_references_table():
  with SqliteDatabase(app_settings.EQUIPMENT_DB) as db:
    db.create_table(References)
