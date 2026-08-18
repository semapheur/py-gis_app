from sqlite.table import Field, Table, datetime_field, uuid_field


class References(Table):
  _table_name = "reference"
  id = uuid_field(True, False)
  classification = uuid_field(False, False)
  releasability = uuid_field(False, False)
  datetime_released = datetime_field(False)
  source_type = Field(str, nullable=False)
  originator = Field(str, nullable=False)
  title = Field(str, nullable=False)
  url = Field(str, nullable=True)
