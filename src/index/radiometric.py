import json
from typing import Literal, TypedDict

from src.const import INDEX_DB
from src.spatialite import HASH_FIELD, ColumnType, Field, Model, SqliteDatabase


class NoiseParameters(TypedDict):
  type: Literal["ABSOLUTE", "RELATIVE"]
  poly: list[list[float]]


polygon = Field(
  list[list[float]],
  ColumnType.TEXT,
  to_sql=lambda x: json.dumps(x),
  from_sql=lambda x: json.loads(x),
)


class RadiometricParamsTable(Model):
  _table_name = "radiometric_params"
  id = HASH_FIELD
  noise = polygon
  sigma0 = polygon
  beta0 = polygon
  gamma0 = polygon


def get_radiometric_parameters(
  hash_id: bytes, factors: tuple[Literal["noise", "sigma0", "beta0", "gamma0"], ...]
):
  with SqliteDatabase(INDEX_DB) as db:
    rows = db.select_records(
      RadiometricParamsTable,
      columns=factors,
      where="id = :id",
      params={"id": hash_id},
      to_json=True,
    )
    return rows[0]
