from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.table import Field, Table, hash_field

app_settings = get_settings()


class RpcTable(Table):
  _table_name = "rpc"
  id = hash_field(True)
  # Error estimates
  err_bias = Field(float)
  err_random = Field(float)
  # Pixel normalization
  line_offset = Field(float)
  line_scale = Field(float)
  sample_offset = Field(float)
  sample_scale = Field(float)
  # Geographic normalization
  latitude_offset = Field(float)
  latitude_scale = Field(float)
  longitude_offset = Field(float)
  longitude_scale = Field(float)
  height_offset = Field(float)
  height_scale = Field(float)
  # RPC coefficients
  line_numerator_coefficients = Field(str)
  line_denominator_coefficients = Field(str)
  sample_numerator_coefficients = Field(str)
  sample_denominator_coefficients = Field(str)
  # Optional geographic bounds
  min_latitude = Field(float)
  max_latitude = Field(float)
  min_longitude = Field(float)
  max_longitude = Field(float)
  # Optional height bounds
  height_min = Field(float)
  height_max = Field(float)


def create_radiometric_table():
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    db.create_table(RpcTable)
