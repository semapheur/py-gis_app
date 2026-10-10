# from functools import lru_cache
# from typing import Union

# import rpc_solver
from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase

# from src.sqlite.query_builder import SelectQuery
from src.sqlite.table import Field, Table, hash_field, json_field

app_settings = get_settings()


class RpcTable(Table):
  _table_name = "rpc"
  id = hash_field(True)
  # Error estimates
  err_bias = Field(float)
  err_random = Field(float)
  # Pixel normalization
  line_offset = Field(float, nullable=False)
  line_scale = Field(float, nullable=False)
  sample_offset = Field(float, nullable=False)
  sample_scale = Field(float, nullable=False)
  # Geographic normalization
  latitude_offset = Field(float, nullable=False)
  latitude_scale = Field(float, nullable=False)
  longitude_offset = Field(float, nullable=False)
  longitude_scale = Field(float, nullable=False)
  height_offset = Field(float, nullable=False)
  height_scale = Field(float, nullable=False)
  # RPC coefficients
  line_numerator_coefficients = json_field(list[float], nullable=False)
  line_denominator_coefficients = json_field(list[float], nullable=False)
  sample_numerator_coefficients = json_field(list[float], nullable=False)
  sample_denominator_coefficients = json_field(list[float], nullable=False)


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


"""
@lru_cache(maxsize=128)
def get_rpc_model(image_hash: bytes) -> rpc_solver.RPCModel:
  query = (
    SelectQuery()
    .select(*RpcTable.column_sql())
    .from_(RpcTable._table_name)
    .where("id = ?", image_hash)
  )
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    rpc_rows = db.select_models(RpcTable, query)

  if not rpc_rows:
    raise LookupError(f"No RPC metadata for image {image_hash.hex()}")

  return rpc_solver.RPCModel(rpc_rows[0])


def get_geo_coordinates(
  image_hash: bytes, pixel: tuple[float, float], height: float = 0.0
) -> tuple[float, float, float]:

  rpc_model = get_rpc_model(image_hash)
  return rpc_model.pixel_to_geo(pixel[0], pixel[1], height)
"""
