import os
import sqlite3
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Literal, Mapping, Optional, TypeAlias, Union

from src.env import load_env

load_env()

SqliteTypes: TypeAlias = Union[bytes, int, float, str]

Geometry: TypeAlias = Literal[
  "POINT",
  "LINESTRING",
  "POLYGON",
  "MULTIPOINT",
  "MULTILINESTRING",
  "MULTIPOLYGON",
  "GEOMETRYCOLLECTION",
]


class ColumnType(Enum):
  INTEGER = "INTEGER"
  REAL = "REAL"
  TEXT = "TEXT"
  BLOB = "BLOB"


class Field:
  type_map: dict[type, str] = {
    int: ColumnType.INTEGER.value,
    float: ColumnType.REAL.value,
    str: ColumnType.TEXT.value,
    bytes: ColumnType.BLOB.value,
  }

  def __init__(
    self,
    type_: type,
    primary_key: bool = False,
    nullable: bool = True,
    default: Optional[SqliteTypes] = None,
    geometry_type: Optional[Geometry] = None,
  ):
    if type_ not in self.type_map:
      raise ValueError(f"Unsupported field type: {type_}")

    self.type_ = type_
    self.primary_key = primary_key
    self.nullable = nullable
    self.default = default
    self.geometry_type = geometry_type

  def sql_type(self) -> str:
    return self.type_map[self.type_]


class ModelMeta(type):
  def __new__(cls, name, bases, attributes):
    fields: dict[str, Field] = {}
    for k, v in list(attributes.items()):
      if isinstance(v, Field):
        fields[k] = v
        del attributes[k]

    attributes["_fields"] = fields
    return super().__new__(cls, name, bases, attributes)


class Model(metaclass=ModelMeta):
  table_name: Optional[str] = None
  _fields: dict[str, Field] = {}

  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    if cls.table_name is None:
      cls.table_name = cls.__name__.lower()

  @classmethod
  def create_table_sql(cls) -> str:
    if not cls.table_name:
      raise ValueError(f"{cls.__name__} must define table_name")

    columns: list[str] = []
    for name, field in cls._fields.items():
      if field.geometry_type is not None:
        continue

      col_def = f"{name} {field.sql_type()}"

      if field.primary_key:
        col_def = f"{name} INTEGER PRIMARY KEY"
      elif not field.nullable:
        col_def += " NOT NULL"

      if field.default is not None:
        col_def += f" DEFAULT {field.default}"

      columns.append(col_def)

    if not columns:
      raise ValueError(f"{cls.__name__} has no fields")

    columns_sql = ", ".join(columns)
    return f"CREATE TABLE IF NOT EXISTS {cls.table_name} ({columns_sql})"

  @classmethod
  def add_geometry_sql(cls, srid=4326, dimension: str = "XY") -> list[str]:
    if not cls.table_name:
      raise ValueError(f"{cls.__name__} must define table_name")

    sql: list[str] = []

    for name, field in cls.geometry_fields().items():
      sql.append(f"""
        SELECT AddGeometryColumn('{cls.table_name}', '{name}', {srid}, '{field.geometry_type}', '{dimension}')
      """)

    return sql

  @classmethod
  def geometry_fields(cls) -> dict[str, Field]:
    return {
      name: field
      for name, field in cls._fields.items()
      if field.geometry_type is not None
    }


@contextmanager
def spatialite_connect(db_path: Path):
  extensions = {".db", ".sqlite"}
  if not db_path.parent.exists() or db_path.suffix.lower() not in extensions:
    raise ValueError(f"Invalid database path: {str(db_path)}")

  db = sqlite3.connect(db_path)

  try:
    db.enable_load_extension(True)
    db.load_extension(os.environ["SPATIALITE"])

    cursor = db.cursor()

    cursor.execute("""
      SELECT name FROM sqlite_master
      WHERE type='table' AND name='spatial_ref_sys';
    """)
    meta_exists = cursor.fetchone() is not None
    if not meta_exists:
      cursor.execute("SELECT InitSpatialMetaData(1);")
      db.commit()

    yield db
    db.commit()

  finally:
    db.close()


def insert_records(
  db: sqlite3.Connection,
  table: str,
  rows: list[Mapping[str, SqliteTypes]],
  geometry_column: str,
  srid=4326,
):
  columns = list(rows[0].keys())
  placeholders: list[str] = []
  for col in columns:
    if col == geometry_column:
      placeholders.append(f"GeomFromText(:{col}, {srid})")
    else:
      placeholders.append(f":{col}")

  columns_sql = ", ".join(columns)
  placeholder_sql = ", ".join(placeholders)

  sql = f"INSERT INTO {table} ({columns_sql}) VALUES ({placeholder_sql})"

  db.cursor().executemany(sql, rows)
