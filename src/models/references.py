from bootstrap import get_settings
from sqlite.connect import SqliteDatabase
from sqlite.table import Field, Table, datetime_field, uuid_field

app_settings = get_settings()


class References(Table):
  _table_name = "reference"
  id = uuid_field(True, False)
  classification = uuid_field(False, False)
  releasability = uuid_field(False, False)
  datetime_released = datetime_field(False)
  source_type = Field(str, nullable=False)
  originator = uuid_field(False, False)
  discipline = uuid_field(False, False)
  title = Field(str, nullable=False)
  url = Field(str, nullable=True)


class Originator(Table):
  _table_name = "orignator"
  id = uuid_field(True, False)
  name = Field(str, nullable=False)
  name_short = Field(str, nullable=True)
  country = Field(str, nullable=False)


class Discipline(Table):
  _table_name = "discipline"
  id = uuid_field(True, False)
  name = Field(str, nullable=False, unique=True)
  name_short = Field(str, nullable=False)


class SourceType(Table):
  _table_name = "source_type"
  id = uuid_field(True, False)
  name = Field(str, nullable=False, unique=True)
  name_short = Field(str, nullable=False)


def create_references_table():
  with SqliteDatabase(app_settings.REFERENCE_DB) as db:
    db.create_table(References)
    db.create_table(Originator)
    db.create_table(Discipline)
    db.create_table(SourceType)
