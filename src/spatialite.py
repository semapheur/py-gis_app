from __future__ import annotations

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import (
  Any,
  Callable,
  Generic,
  Literal,
  Mapping,
  Optional,
  Sequence,
  TypedDict,
  TypeVar,
  Union,
)

from src.hashing import encode_sha256_to_b64
from src.timeutils import datetime_to_unix, unix_to_datetime

SqliteValue = Union[bytes, int, float, str, None]

T = TypeVar("T")
S = TypeVar("S")
J = TypeVar("J")

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

  @classmethod
  def from_python(cls, py_type: type) -> ColumnType:
    for ct in cls:
      if ct.value is py_type:
        return ct

    raise ValueError(f"No SQLite affinity for python type {py_type!r}")


@dataclass(slots=True)
class Field(Generic[T, S, J]):
  python_type: type[T]
  sql_type: Optional[ColumnType] = None
  primary_key: bool = False
  nullable: bool = True
  unique: bool = False
  default: Optional[S] = None
  geometry_type: Optional[Geometry] = None
  srid: int = 4326
  to_sql: Optional[Callable[[T], S]] = None
  from_sql: Optional[Callable[[S], T]] = None
  to_json: Optional[Callable[[T], J]] = None
  from_json: Optional[Callable[[J], T]] = None

  def __post_init__(self):
    if self.sql_type is None:
      self.sql_type = ColumnType.from_python(self.python_type)

    if self.primary_key:
      self.nullable = False

  def sql_column_type(self):
    if self.sql_type is None:
      raise ValueError("sql_type is not set")

    return self.sql_type.name

  def validate_nullability(self, value: Optional[Any]):
    if value is None and not self.nullable:
      raise ValueError(f"Field {self!r} is non-nullable but received None")

  def serialize_to_sql(self, value: Optional[T]) -> Union[S, None]:
    self.validate_nullability(value)

    if value is None:
      return None

    if self.to_sql:
      return self.to_sql(value)

    return value

  def deserialize_from_sql(self, value: S) -> Union[T, None]:
    if value is None:
      return None

    if self.from_sql:
      return self.from_sql(value)

    return self.python_type(value)

  def serialize_to_json(self, value: Optional[T]) -> Union[J, None]:
    self.validate_nullability(value)

    if value is None:
      return None

    if self.to_json:
      return self.to_json(value)

    return value

  def deserialize_from_json(self, value: J) -> Union[T, None]:
    self.validate_nullability(value)

    if value is None:
      return None

    if self.from_json:
      return self.from_json(value)

    return self.python_type(value)

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
  _table_name: Optional[str] = None
  _fields: dict[str, Field] = {}

  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    if cls._table_name is None:
      cls._table_name = cls.__name__.lower()

  def to_dict(self, json: bool = False) -> dict[str, SqliteValue]:
    data: dict[str, Any] = {}

    for name, field in self._fields.items():
      value = getattr(self, name, None)

      if field.geometry_type is not None:
        data[name] = field.to_wkt(value)
      else:
        data[name] = field.serialize_to_json(value) if json else value

    return data

  @classmethod
  def rowid(cls) -> Union[str, None]:
    for name, field in cls._fields.items():
      if field.primary_key:
        return name

    return None

  @classmethod
  def create_table_sql(cls) -> str:
    if not cls._table_name:
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
    return f"CREATE TABLE IF NOT EXISTS {cls._table_name} ({columns_sql})"

  @classmethod
  def add_geometry_sql(cls, dimension: str = "XY") -> list[str]:
    if not cls._table_name:
      raise ValueError(f"{cls.__name__} must define table_name")

    sql: list[str] = []

    for name, field in cls.geometry_fields().items():
      sql.append(f"""
        SELECT AddGeometryColumn('{cls._table_name}', '{name}', {field.srid}, '{field.geometry_type}', '{dimension}')
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
      value = field.deserialize_from_sql(raw)
      setattr(obj, name, value)

    return obj

  @classmethod
  def from_dict(cls, data: dict[str, SqliteValue], json: bool = False):
    obj = cls.__new__(cls)

    for name, field in cls._fields.items():
      if name in data:
        value = field.deserialize_from_json(data[name]) if json else data[name]
      elif field.default is not None:
        value = field.default
      elif not field.nullable and not field.primary_key:
        raise ValueError(f"{cls.__name__}.{name} is required")
      else:
        value = None

      setattr(obj, name, value)

    return obj


class SqliteDatabase:
  def __init__(self, db_path: Path, spatial: bool = False):
    self.db_path = db_path
    self.spatial = spatial
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

    if self.spatial:
      self.conn.enable_load_extension(True)
      self.conn.load_extension(os.environ["SPATIALITE"])
      self._ensure_spatial_metadata()

  def _close(self):
    if self.conn:
      self.conn.commit()
      self.conn.close()
    self.conn = None

  def _check_connection(self):
    if self.conn is None:
      raise RuntimeError("Database not connected")

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

  def create_fts_table(self, table: type[Model], columns: Sequence[str]):
    self._check_connection()

    table_name = table._table_name
    fts_name = f"{table_name}_fts"
    rowid = table.rowid()
    fts_columns = ",".join(columns)
    fts_options = f"{fts_columns}content='{table_name}'content_rowid='{rowid}'"

    create_sql = (
      f"""CREATE VIRTUAL TABLE IF NOT EXISTS {fts_name} USING fts5({fts_options})"""
    )

    new = [f"new.{c}" for c in columns]

    trigger_after_insert = f"""
    CREATE TRIGGER {table_name}_ai AFTER INSERT ON {table_name}
    BEGIN
      INSERT INTO {fts_name}({rowid}, {fts_columns})
      VALUES ({new});
    END
    """

    update_parts = [f"{c} = new.{c}" for c in columns]
    trigger_after_update = f"""CREATE TRIGGER {table_name}_au AFTER UPDATE ON {table_name}
    BEGIN
      UPDATE {fts_name}
      SET {",".join(update_parts)}
      WHERE rowid = new.{rowid};
    END
    """

    trigger_after_delete = f"""
      CREATE TRIGGER {table_name}_ad AFTER DELETE ON {table_name}
      BEGIN
        DELETE FROM {fts_name}
        WHERE rowid = old.{rowid};
      END
    """

    cursor = self.conn.cursor()
    cursor.execute(create_sql)
    cursor.execute(trigger_after_insert)
    cursor.execute(trigger_after_update)
    cursor.execute(trigger_after_delete)

  def list_tables(self, include_internal: bool = False) -> list[str]:
    self._check_connection()

    sql = "SELECT name FROM sqlite_master WHERE type = 'table'"

    if not include_internal:
      patterns = ("sqlite_%", "spatial_%", "idx_%")
      for pattern in patterns:
        sql += f" AND name NOT LIKE '{pattern}'"

    sql += " ORDER BY name"

    cursor = self.conn.cursor()
    cursor.execute(sql)
    return [row[0] for row in cursor.fetchall()]

  def insert_models(
    self,
    models: Sequence[Model],
    on_conflict: Optional[OnConflict] = None,
    returning: Optional[str] = None,
  ) -> Union[list[Any], None]:
    self._check_connection()

    if not models:
      return

    table = type(models[0])
    table_name = table._table_name
    geometry_fields = table.geometry_fields()

    rows = []
    for obj in models:
      row = {}
      for name, field in obj._fields.items():
        value = getattr(obj, name, None)
        if name in geometry_fields:
          row[name] = field.to_wkt(value)
        else:
          row[name] = field.serialize_to_sql(value)

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
    params: Optional[Union[dict[str, SqliteValue], tuple[SqliteValue, ...]]] = None,
  ):
    self._check_connection

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

    sql_parts.append(f"SELECT {column_sql} FROM {table._table_name}")

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
    params: Optional[Union[dict[str, SqliteValue], tuple[SqliteValue, ...]]] = None,
  ) -> list[Model]:
    rows, _ = self._select_rows(
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
    params: Optional[Union[dict[str, SqliteValue], tuple[SqliteValue, ...]]] = None,
    to_json: bool = False,
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

    results: list[dict[str, SqliteValue]] = []
    for row in rows:
      result_row = {}
      for i, col in enumerate(return_columns):
        field = table._fields.get(col)
        if field is None:
          result_row[col] = row[i]
          continue

        if field.geometry_type is None:
          value = field.deserialize_from_sql(row[i])
        else:
          value = json.loads(row[i]) if geo_format == "AsGeoJSON" else row[i]

        result_row[col] = field.serialize_to_json(value) if to_json else value

      results.append(result_row)

    return results

  def delete_by_ids(self, table: type[Model], ids: list[Any]) -> int:
    self._check_connection()

    table_name = table._table_name

    pk_field = None
    pk_name = None

    for name, field in table._fields.items():
      if field.primary_key:
        pk_field = field
        pk_name = name
        break

    if pk_field is None or pk_name is None:
      raise ValueError(f"{table.__name__} has no primary key field")

    id_type = pk_field.sql_column_type()

    cursor = self.conn.cursor()

    cursor.execute(f"""
      CREATE TEMPORARY TABLE IF NOT EXISTS temp_delete_ids (
        id {id_type}
      )
    """)

    cursor.execute("DELETE FROM temp_delete_ids")

    serialized_ids = []
    for i in ids:
      serialized = pk_field.serialize_to_sql(i)
      serialized_ids.append((serialized,))

    cursor.executemany("INSERT INTO temp_delete_ids (id) VALUES (?)", serialized_ids)

    cursor.execute(f"""
      DELETE FROM {table_name}
      WHERE {pk_name} IN (SELECT id FROM temp_delete_ids)
    """)

    rows_deleted = cursor.rowcount

    cursor.execute("DROP TABLE temp_delete_ids")
    self.conn.commit()
    return rows_deleted


def table_exists(db: sqlite3.Connection, table: type[Model]) -> bool:
  table_name = table._table_name
  cursor = db.cursor()

  cursor.execute(
    """
    SELECT name FROM sqlite_master
    WHERE type='table' AND name=?
  """,
    (table_name,),
  )
  return cursor.fetchone() is not None


def get_tables(db_path: Path) -> list[str]:
  with SqliteDatabase(db_path) as db:
    return db.list_tables()


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
  rows: list[Mapping[str, SqliteValue]],
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


HASH_FIELD = Field(
  bytes,
  sql_type=ColumnType.BLOB,
  primary_key=True,
  to_json=lambda x: encode_sha256_to_b64(x),
)

UUID_FIELD = Field(
  uuid.UUID,
  sql_type=ColumnType.BLOB,
  primary_key=True,
  to_sql=lambda u: u.bytes,
  from_sql=lambda b: uuid.UUID(bytes=b),
  to_json=lambda u: str(u),
  from_json=lambda u: uuid.UUID(u),
)


def datetime_field(nullable: bool):
  return Field(
    datetime,
    ColumnType.INTEGER,
    nullable=nullable,
    to_sql=lambda x: datetime_to_unix(x),
    from_sql=lambda x: unix_to_datetime(x),
    to_json=lambda x: datetime_to_unix(x),
    from_json=lambda x: unix_to_datetime(x),
  )


def path_field(nullable: bool, unique: bool):
  return Field(
    Path,
    sql_type=ColumnType.TEXT,
    nullable=nullable,
    unique=unique,
    to_sql=lambda x: str(x),
    from_sql=lambda x: Path(x),
    to_json=lambda x: str(x),
    from_json=lambda x: Path(x),
  )


def enum_field(enum: type[Enum], sql_type: ColumnType):
  return Field(
    enum,
    sql_type,
    to_sql=lambda x: x.value,
    from_sql=lambda x: enum(x),
    to_json=lambda x: x.value if isinstance(x, enum) else x,
    from_json=lambda x: enum(x),
  )
