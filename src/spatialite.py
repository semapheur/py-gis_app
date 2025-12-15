from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import (
  Any,
  Callable,
  Literal,
  Mapping,
  Optional,
  Sequence,
  TypedDict,
  Union,
)

SqliteTypes = Union[bytes, int, float, str, None]

GeoFormat = Literal["AsText", "AsGeoJSON"]

Geometry = Literal[
  "POINT",
  "LINESTRING",
  "POLYGON",
  "MULTIPOINT",
  "MULTILINESTRING",
  "MULTIPOLYGON",
  "GEOMETRYCOLLECTION",
]


class OnConflict(TypedDict):
  index: str
  action: str


class JoinClause(TypedDict):
  join_type: Literal["LEFT", "INNER", "CROSS"]
  expression: str


class ColumnType(Enum):
  INTEGER = int
  REAL = float
  TEXT = str
  BLOB = bytes


class Field:
  def __init__(
    self,
    type_: type,
    sql_type: Optional[type] = None,
    primary_key: bool = False,
    nullable: bool = True,
    unique: bool = False,
    default: Optional[SqliteTypes] = None,
    geometry_type: Optional[Geometry] = None,
    srid: int = 4326,
    to_sql: Optional[Callable[[Any], Any]] = None,
    to_python: Optional[Callable[[Any], Any]] = None,
  ):
    self.type_ = type_

    if sql_type is None:
      if type_ not in (m.value for m in ColumnType):
        raise ValueError(
          f"sql_type must be provided for unsupported python type: {type_}"
        )
      self.sql_type = ColumnType(type_)
    else:
      self.sql_type = ColumnType(sql_type)

    self.primary_key = primary_key
    self.nullable = nullable
    self.unique = unique
    self.default = default
    self.geometry_type = geometry_type
    self.srid = srid
    self.to_sql = to_sql
    self.to_python = to_python

  def sql_column_type(self) -> str:
    return self.sql_type.name

  def serialize(self, value: Any) -> SqliteTypes:
    if value is None:
      return None

    if self.to_sql:
      return self.to_sql(value)

    if not isinstance(value, self.type_):
      raise TypeError(f"Excpted {self.type_}, got {type(value)}")

    return value

  def deserialize(self, value: Any) -> Any:
    if value is None:
      return None

    if self.to_python:
      return self.to_python(value)

    return self.type_(value)

  def to_wkt(self, value: Optional[str]) -> Optional[str]:
    if self.geometry_type is None:
      raise NotImplementedError("Attempted to convert a non-geometry value to WKT")

    if value is None:
      return None

    if not isinstance(value, str):
      raise ValueError(f"Geometry field expects WKT string, got {type(value)}")

    return value


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

  def to_dict(self) -> dict[str, SqliteTypes]:
    data = {}

    for name, field in self._fields.items():
      value = getattr(self, name, None)

      if field.geometry_type is not None:
        data[name] = field.to_wkt(value)
      else:
        data[name] = field.serialize(value)

    return data

  @classmethod
  def create_table_sql(cls) -> str:
    if not cls.table_name:
      raise ValueError(f"{cls.__name__} must define table_name")

    columns: list[str] = []
    for name, field in cls._fields.items():
      if field.geometry_type is not None:
        continue

      col_def = [name, field.sql_column_type()]

      if field.primary_key:
        col_def.append("PRIMARY KEY")
      elif not field.nullable:
        col_def.append("NOT NULL")
      elif field.unique:
        col_def.append("UNIQUE")

      if field.default is not None:
        col_def.append(f"DEFAULT {field.default}")

      columns.append(" ".join(col_def))

    if not columns:
      raise ValueError(f"{cls.__name__} has no fields")

    columns_sql = ", ".join(columns)
    return f"CREATE TABLE IF NOT EXISTS {cls.table_name} ({columns_sql})"

  @classmethod
  def add_geometry_sql(cls, dimension: str = "XY") -> list[str]:
    if not cls.table_name:
      raise ValueError(f"{cls.__name__} must define table_name")

    sql: list[str] = []

    for name, field in cls.geometry_fields().items():
      sql.append(f"""
        SELECT AddGeometryColumn('{cls.table_name}', '{name}', {field.srid}, '{field.geometry_type}', '{dimension}')
      """)

    return sql

  @classmethod
  def geometry_fields(cls) -> dict[str, Field]:
    return {
      name: field
      for name, field in cls._fields.items()
      if field.geometry_type is not None
    }

  @classmethod
  def from_row(cls, row, columns=None) -> Model:
    if columns is None:
      columns = list(cls._fields.keys())

    obj = cls.__new__(cls)

    for i, name in enumerate(columns):
      field = cls._fields[name]
      raw = row[i]
      value = field.deserialize(raw)
      setattr(obj, name, value)

    return obj


class SpatialDatabase:
  def __init__(self, db_path: Path):
    self.db_path = db_path
    self.conn = None

  def __enter__(self):
    self._open()
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self._close()

  def _open(self):
    if not self.db_path.parent.exists():
      raise FileNotFoundError(f"Directory does not exist: {self.db_path.parent}")

    if self.db_path.suffix.lower() not in {".db", ".sqlite"}:
      raise ValueError(f"Invalid db path: {self.db_path}")

    self.conn = sqlite3.connect(self.db_path)
    self.conn.enable_load_extension(True)
    self.conn.load_extension(os.environ["SPATIALITE"])
    self._ensure_spatial_metadata()

  def _close(self):
    if self.conn:
      self.conn.commit()
      self.conn.close()
    self.conn = None

  def _ensure_spatial_metadata(self):
    if self.conn is None:
      raise RuntimeError("Database not connected")

    cursor = self.conn.cursor()
    cursor.execute("""
      SELECT name FROM sqlite_master
      WHERE type='table' AND name='spatial_ref_sys'
    """)
    exists = cursor.fetchone() is not None
    if not exists:
      cursor.execute("SELECT InitSpatialMetaData(1)")
      self.conn.commit()

  def create_table(self, table: type[Model]):
    if self.conn is None:
      raise RuntimeError("Database not connected")

    if table_exists(self.conn, table):
      return

    cursor = self.conn.cursor()
    cursor.execute(table.create_table_sql())

    for sql in table.add_geometry_sql():
      cursor.execute(sql)

  def insert_models(
    self,
    models: Sequence[Model],
    on_conflict: Optional[OnConflict] = None,
    returning: Optional[str] = None,
  ) -> Union[list[Any], None]:
    if self.conn is None:
      raise RuntimeError("Database not connected")

    if not models:
      return

    table = type(models[0])
    table_name = table.table_name
    geometry_fields = table.geometry_fields()

    rows = []
    for obj in models:
      row = {}
      for name, field in obj._fields.items():
        value = getattr(obj, name, None)
        if name in geometry_fields:
          row[name] = field.to_wkt(value)
        else:
          row[name] = value if field.to_sql is None else field.to_sql(value)

      rows.append(row)

    columns = list(rows[0].keys())
    placeholders = [
      f"GeomFromText(:{col}, {geometry_fields[col].srid})"
      if col in geometry_fields
      else f":{col}"
      for col in columns
    ]

    columns_sql = ", ".join(columns)
    placeholder_sql = ", ".join(placeholders)
    sql_parts = [f"INSERT INTO {table_name} ({columns_sql}) VALUES ({placeholder_sql})"]

    if on_conflict is not None:
      sql_parts.append(
        f"ON CONFLICT ({on_conflict['index']}) DO {on_conflict['action']}"
      )

    if returning is not None:
      sql_parts.append(f"RETURNING {returning}")

    sql = " ".join(sql_parts)
    cursor = self.conn.cursor()

    if returning is not None:
      results = []
      for row in rows:
        cursor.execute(sql, row)
        results.append(cursor.fetchone())
      self.conn.commit()
      return results

    self.conn.cursor().executemany(sql, rows)
    self.conn.commit()
    return

  def _select_rows(
    self,
    table: type[Model],
    columns: Optional[Union[Literal["*"], tuple[str, ...]]] = None,
    geo_format: GeoFormat = "AsGeoJSON",
    derived: Optional[dict[str, str]] = None,
    with_clause: Optional[str] = None,
    join: Optional[JoinClause] = None,
    where: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    params: Optional[Union[dict[str, SqliteTypes], tuple[SqliteTypes, ...]]] = None,
  ):
    if self.conn is None:
      raise RuntimeError("Database not connected")

    table_columns = list(table._fields.keys())

    def validate_columns(columns: tuple[str, ...], table: type[Model]):
      bad_columns = set(columns).difference(table._fields.keys())
      if not bad_columns:
        return

      raise ValueError(
        f"Invalid column(s) for {table.__name__}: {bad_columns}"
        f"Valid columns are: {table_columns}"
      )

    if isinstance(columns, tuple):
      validate_columns(columns, table)

    else:
      columns = tuple() if columns is None else tuple(table_columns)

    geometry_fields = table.geometry_fields()

    sql_columns: list[str] = []
    returned_columns: list[str] = []
    for col in columns:
      if col in geometry_fields:
        sql_columns.append(f"{geo_format}({col}) AS {col}")
      else:
        sql_columns.append(col)

      returned_columns.append(col)

    if derived is not None:
      for alias, expr in derived.items():
        sql_columns.append(f"{expr} AS {alias}")
        returned_columns.append(alias)

    column_sql = ", ".join(sql_columns)

    sql_parts: list[str] = []
    if with_clause is not None:
      sql_parts.append(f"WITH {with_clause}")

    sql_parts.append(f"SELECT {column_sql} FROM {table.table_name}")

    if join is not None:
      sql_parts.append(f"{join['join_type']} JOIN {join['expression']}")

    if where is not None:
      sql_parts.append(f"WHERE {where}")

    if limit is not None:
      sql_parts.append(f"LIMIT {limit}")

    if offset is not None:
      sql_parts.append(f"OFFSET {offset}")

    sql = " ".join(sql_parts)
    cursor = self.conn.cursor()
    rows = cursor.execute(sql, params or {}).fetchall()

    return rows, returned_columns

  def select_models(
    self,
    table: type[Model],
    columns: Optional[Union[Literal["*"], tuple[str, ...]]] = None,
    geo_format: GeoFormat = "AsGeoJSON",
    with_clause: Optional[str] = None,
    where: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    params: Optional[Union[dict[str, SqliteTypes], tuple[SqliteTypes, ...]]] = None,
  ) -> list[Model]:
    rows, return_columns = self._select_rows(
      table,
      columns=columns,
      geo_format=geo_format,
      with_clause=with_clause,
      where=where,
      limit=limit,
      offset=offset,
      params=params,
    )

    return [table.from_row(row, columns) for row in rows]

  def select_records(
    self,
    table: type[Model],
    columns: Optional[Union[Literal["*"], tuple[str, ...]]] = None,
    geo_format: GeoFormat = "AsGeoJSON",
    derived: Optional[dict[str, str]] = None,
    with_clause: Optional[str] = None,
    join: Optional[JoinClause] = None,
    where: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    params: Optional[Union[dict[str, SqliteTypes], tuple[SqliteTypes, ...]]] = None,
  ) -> list[dict[str, Any]]:
    rows, return_columns = self._select_rows(
      table,
      columns=columns,
      geo_format=geo_format,
      derived=derived,
      with_clause=with_clause,
      join=join,
      where=where,
      limit=limit,
      offset=offset,
      params=params,
    )

    results: list[dict[str, SqliteTypes]] = []
    for row in rows:
      result_row = {}
      for i, col in enumerate(return_columns):
        field = table._fields.get(col)
        if field is None:
          result_row[col] = row[i]
          continue

        if field.geometry_type is None:
          value = field.deserialize(row[i])
        else:
          value = json.loads(row[i]) if geo_format == "AsGeoJSON" else row[i]

        result_row[col] = value

      results.append(result_row)

    return results


def table_exists(db: sqlite3.Connection, table: type[Model]) -> bool:
  table_name = table.table_name
  cursor = db.cursor()

  cursor.execute(
    """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
  """,
    (table_name,),
  )
  return cursor.fetchone() is not None


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
