from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.table import Field, Table, hash_field

app_settings = get_settings()


class RpcTable(Table):
  _table_name = "rpc"
  id = hash_field(True)
  err_bias = Field(float)
  err_rand = Field(float)
  line_off = Field(float)
  line_scale = Field(float)
  samp_off = Field(float)
  samp_scale = Field(float)
  lat_off = Field(float)
  lat_scale = Field(float)
  lon_off = Field(float)
  lon_scale = Field(float)
  height_off = Field(float)
  height_scale = Field(float)
  line_num = Field(str)
  line_den = Field(str)
  samp_num = Field(str)
  samp_den = Field(str)


def create_radiometric_table():
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    db.create_table(RpcTable)
