from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.table import Field, Table, hash_field, json_field

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
  line_numerator_coefficients = json_field(list[float])
  line_denominator_coefficients = json_field(list[float])
  sample_numerator_coefficients = json_field(list[float])
  sample_denominator_coefficients = json_field(list[float])


def create_radiometric_table():
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    db.create_table(RpcTable)


def validate_rpc(rpc: RpcTable) -> bool:
  return (
    all(
      len(c) == 20
      for c in (
        rpc.line_numerator_coefficients,
        rpc.line_denominator_coefficients,
        rpc.sample_numerator_coefficients,
        rpc.sample_denominator_coefficients,
      )
    )
    and rpc.line_scale not in (None, 0)
    and rpc.sample_scale not in (None, 0)
  )


def get_gdal_rpc(gdal_info: dict, image_hash: bytes) -> RpcTable | None:
  rpc = gdal_info.get("metadata", {}).get("RPC")
  if not rpc:
    return None

  def f(key: str) -> float | None:
    v = rpc.get(key)
    return float(v) if v is not None else None

  def coeffs(key: str) -> list[float]:
    return [float(c) for c in rpc[key].split()]

  return RpcTable().from_dict(
    {
      "id": image_hash,
      "err_bias": f("ERR_BIAS"),
      "err_random": f("ERR_RAND"),
      "line_offset": f("LINE_OFF"),
      "line_scale": f("LINE_SCALE"),
      "sample_offset": f("SAMP_OFF"),
      "sample_scale": f("SAMP_SCALE"),
      "latitude_offset": f("LAT_OFF"),
      "latitude_scale": f("LAT_SCALE"),
      "longitude_offset": f("LONG_OFF"),
      "longitude_scale": f("LONG_SCALE"),
      "height_offset": f("HEIGHT_OFF"),
      "height_scale": f("HEIGHT_SCALE"),
      "line_numerator_coefficients": coeffs("LINE_NUM_COEFF"),
      "line_denominator_coefficients": coeffs("LINE_DEN_COEFF"),
      "sample_numerator_coefficients": coeffs("SAMP_NUM_COEFF"),
      "sample_denominator_coefficients": coeffs("SAMP_DEN_COEFF"),
    }
  )
