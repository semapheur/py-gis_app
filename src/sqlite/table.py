from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, StrEnum
from pathlib import Path
from sqlite3 import Row
from typing import (
  Any,
  Callable,
  Generic,
  Literal,
  Optional,
  TypeVar,
  Union,
)

from src.hashing import decode_sha256_from_b64, encode_sha256_to_b64
from src.timeutils import datetime_to_unix, unix_to_datetime

SqliteValue = Union[bytes, int, float, str, None]

T = TypeVar("T")
S = TypeVar("S", bytes, int, float, str, None)
J = TypeVar("J")

GeoFormat = Literal["AsText", "AsGeoJSON"]

ForeignKeyAction = Literal["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"]

_EWKT_PREFIX = re.compile(r"^\s*SRID=(\d+);", re.IGNORECASE)
_WKT_TYPE = re.compile(r"^\s*([A-Za-z]+)\s*(Z|M|ZM)?\s*(\(|EMPTY)", re.IGNORECASE)


class Geometry(StrEnum):
  POINT = "POINT"
  LINESTRING = "LINESTRING"
  POLYGON = "POLYGON"
  MULTIPOINT = "MULTIPOINT"
  MULTILINESTRING = "MULTILINESTRING"
  MULTIPOLYGON = "MULTIPOLYGON"
  GEOMETRYCOLLECTION = "GEOMETRYCOLLECTION"


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
class ForeignKey:
  table: str
  column: str
  on_delete: ForeignKeyAction = "CASCADE"
  on_update: ForeignKeyAction = "NO ACTION"

  def sql(self, column_name: str) -> str:
    return (
      f"FOREIGN KEY ({column_name}) REFERENCES {self.table}({self.column}) "
      f"ON DELETE {self.on_delete} ON UPDATE {self.on_update}"
    )


@dataclass(slots=True)
class Field(Generic[T, S, J]):
  python_type: type[T]
  sql_type: Optional[ColumnType] = None
  primary_key: bool = False
  nullable: bool = True
  unique: bool = False
  foreign_key: Optional[ForeignKey] = None
  default: Optional[S] = None
  to_sql: Optional[Callable[[T], S]] = None
  from_sql: Optional[Callable[[S], T]] = None
  to_json: Optional[Callable[[T], J]] = None
  from_json: Optional[Callable[[J], T]] = None
  validators: list[Callable[[Any], None]] = field(default_factory=list)
  name: Optional[str] = None

  def __post_init__(self):
    if self.sql_type is None:
      self.sql_type = ColumnType.from_python(self.python_type)

    if self.primary_key:
      self.nullable = False

  def __set_name__(self, owner, attribute_name: str):
    if self.name is None:
      self.name = attribute_name

  def sql_column_type(self):
    if self.sql_type is None:
      raise ValueError("sql_type is not set")

    return self.sql_type.name

  def check_clauses(self, column: Optional[str] = None) -> list[str]:
    col = column or self.name
    if col is None:
      raise ValueError("Field has no name; cannot build CHECK clauses")

    return [v.sql.format(col=col) for v in self.validators if getattr(v, "sql", None)]

  def validate_nullability(self, value: Optional[Any]):
    if value is None and not self.nullable:
      raise ValueError(f"Field {self.name!r} is non-nullable but received None")

  def validate_type(self, value: Any):
    expected = self.python_type
    if not isinstance(expected, type):
      return

    if expected is int and isinstance(value, bool):
      raise ValueError(f"Field {self.name!r} expects int, got bool")

    if expected is float and isinstance(value, int) and not isinstance(value, bool):
      return

    if not isinstance(value, expected):
      raise TypeError(
        f"Field {self.name!r} expects {expected.__name__}, got {type(value).__name__}"
      )

  def validate(self, value: Optional[Any]):
    self.validate_nullability(value)
    if value is None:
      return

    self.validate_type(value)

    for check in self.validators:
      try:
        check(value)
      except ValueError as e:
        raise ValueError(f"Field [{self.name!r}: {e}") from None

  def serialize_to_sql(self, value: Optional[T]) -> Union[S, None]:
    self.validate(value)

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

    result = self.from_json(value) if self.from_json else self.python_type(value)

    self.validate(result)
    return result


@dataclass(slots=True)
class GeometryField(Field):
  python_type: type[str] = str
  geometry_type: Optional[Geometry] = None
  srid: int = 4326

  def __post_init__(self):
    Field.__post_init__(self)
    if self.geometry_type is None:
      raise ValueError("GeometryField requires a geomtry_type")
    self.validators.append(self._validate_wkt)

  def _expected_geometry_name(self, value: str):
    return str(getattr(self.geometry_type, "name", self.geometry_type)).upper()

  def _validate_wkt(self, value: str):
    text = value
    ewkt = _EWKT_PREFIX.match(text)
    if ewkt:
      if int(ewkt.group(1)) != self.srid:
        raise ValueError(
          f"Field {self.name!r}: SRID {ewkt.group(1)} does not match expected {self.srid}"
        )
      text = text[ewkt.end() :]

    match = _WKT_TYPE.match(text)
    if not match:
      raise ValueError(f"Field {self.name!r}: not valid WKT: {value[:40]!r}")

    actual = match.group(1).upper()
    expected = self._expected_geometry_name()
    if actual != expected:
      raise ValueError(
        f"Field {self.name!r}: expected {expected} geometry, got {actual}"
      )

  def to_wkt(self, value: Optional[str]) -> Optional[str]:
    if self.geometry_type is None:
      raise NotImplementedError("Attempted to convert a non-geometry value to WKT")

    if value is None:
      return None

    if not isinstance(value, str):
      raise ValueError(f"Geometry field expects WKT string, got {type(value)}")

    return value


@dataclass(slots=True)
class Index:
  columns: tuple[str, ...]
  unique: bool = False
  name: Optional[str] = None

  def resolved_name(self, table_name: str) -> str:
    return self.name or f"ix_{table_name}_{'_'.join(self.columns)}"

  def sql(self, table_name: str) -> str:
    index_name = self.resolved_name(table_name)
    unique_kw = "UNIQUE " if self.unique else ""
    columns_sql = ", ".join(self.columns)

    return (
      f"CREATE {unique_kw}INDEX IF NOT EXISTS {index_name} "
      f"ON {table_name} ({columns_sql})"
    )


class TableMeta(type):
  def __new__(cls, name, bases, attributes):
    fields: dict[str, Union[Field, GeometryField]] = {}
    for k, v in list(attributes.items()):
      if isinstance(v, Field):
        if v.name is None:
          v.name = k

        fields[k] = v
        del attributes[k]

    attributes["_fields"] = fields
    attributes["_indexes"] = tuple(attributes.get("_indexes", ()))

    return super().__new__(cls, name, bases, attributes)


class Table(metaclass=TableMeta):
  _table_name: Optional[str] = None
  _fields: dict[str, Union[Field, GeometryField]]
  _indexes: tuple[Index, ...]
  _without_rowid: bool = False

  def __init_subclass__(cls, **kwargs):
    super().__init_subclass__(**kwargs)
    if cls._table_name is None:
      cls._table_name = cls.__name__.lower()

  def to_dict(self, json: bool = False) -> dict[str, SqliteValue]:
    data: dict[str, Any] = {}

    for name, field_ in self._fields.items():
      value = getattr(self, name, None)

      if isinstance(field_, GeometryField):
        data[name] = field_.to_wkt(value)
      else:
        data[name] = field_.serialize_to_json(value) if json else value

    return data

  @classmethod
  def table_name(cls) -> str:
    if cls._table_name is None:
      raise ValueError(f"{cls.__name__} must define table_name")

    return cls._table_name

  @classmethod
  def primary_key_columns(cls) -> tuple[str, ...]:
    return tuple(name for name, field in cls._fields.items() if field.primary_key)

  @classmethod
  def rowid(cls) -> Union[str, None]:
    primary_keys = cls.primary_key_columns()
    return primary_keys[0] if len(primary_keys) == 1 else None

  @classmethod
  def create_table_sql(cls) -> str:
    table_name = cls.table_name()
    primary_keys = cls.primary_key_columns()
    composite_primary_key = len(primary_keys) > 1

    columns: list[str] = []
    constraints: list[str] = []

    for name, field_ in cls._fields.items():
      if isinstance(field, GeometryField):
        continue

      col_def = [name, field_.sql_column_type()]

      if field_.primary_key and not composite_primary_key:
        col_def.append("PRIMARY KEY")
      else:
        if not field_.nullable:
          col_def.append("NOT NULL")

        if field_.unique:
          col_def.append("UNIQUE")

      for clause in field_.check_clauses(name):
        col_def.append(f"CHECK ({clause})")

      if field_.default is not None:
        col_def.append(f"DEFAULT {field_.default}")

      columns.append(" ".join(col_def))

      if field_.foreign_key is not None:
        constraints.append(field_.foreign_key.sql(name))

    if not columns:
      raise ValueError(f"{cls.__name__} has no fields")

    if composite_primary_key:
      constraints.insert(0, f"PRIMARY KEY ({', '.join(primary_keys)})")

    all_defs = columns + constraints
    columns_sql = ", ".join(all_defs)
    without_rowid_sql = " WITHOUT ROWID" if cls._without_rowid else ""

    return f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_sql}){without_rowid_sql}"

  @classmethod
  def create_index_sql(cls) -> list[str]:
    table_name = cls.table_name()
    return [index.sql(table_name) for index in cls._indexes]

  @classmethod
  def add_geometry_sql(cls, dimension: str = "XY") -> list[str]:
    table_name = cls.table_name()

    sql: list[str] = []

    for name, field_ in cls.geometry_fields().items():
      sql.append(f"""
        SELECT AddGeometryColumn('{table_name}', '{name}', {field_.srid}, '{field_.geometry_type}', '{dimension}')
      """)

    return sql

  @classmethod
  def column_names(cls, exclude_geometry_fields: bool = False) -> list[str]:
    return [
      name
      for name, field_ in cls._fields.items()
      if not exclude_geometry_fields or not isinstance(field_, GeometryField)
    ]

  @classmethod
  def geometry_names(cls) -> list[str]:
    return [
      name for name, field_ in cls._fields.items() if isinstance(field_, GeometryField)
    ]

  @classmethod
  def column_sql(cls, geo_format: GeoFormat = "AsGeoJSON") -> list[str]:
    return [
      name
      if not isinstance(field_, GeometryField)
      else f"{geo_format}({name}) AS {name}"
      for name, field_ in cls._fields.items()
    ]

  @classmethod
  def geometry_fields(cls) -> dict[str, GeometryField]:
    return {
      name: field_
      for name, field_ in cls._fields.items()
      if isinstance(field_, GeometryField)
    }

  @classmethod
  def index_columns(cls, index_name: str) -> tuple[str, ...]:
    table_name = cls.table_name()

    for index in cls._indexes:
      if index.resolved_name(table_name) == index_name:
        return index.columns

    raise ValueError(f"No index named '{index_name}' on table '{table_name}'")

  @classmethod
  def from_row(cls, row: Row, columns=None) -> Table:
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
  def from_dict(cls, data: dict[str, Any], json: bool = False):
    obj = cls.__new__(cls)

    for name, field_ in cls._fields.items():
      if name in data:
        value = field_.deserialize_from_json(data[name]) if json else data[name]
      elif field_.default is not None:
        value = field_.default
      elif not field_.nullable and not field_.primary_key:
        raise ValueError(f"{cls.__name__}.{name} is required")
      else:
        value = None

      setattr(obj, name, value)

    return obj


def hash_field(primary: bool):
  return Field(
    bytes,
    sql_type=ColumnType.BLOB,
    primary_key=primary,
    from_json=lambda x: decode_sha256_from_b64(x),
    to_json=lambda x: encode_sha256_to_b64(x),
  )


def uuid_field(primary: bool, nullable: bool):
  return Field(
    uuid.UUID,
    sql_type=ColumnType.BLOB,
    primary_key=primary,
    nullable=False if primary else nullable,
    to_sql=lambda u: u.bytes,
    from_sql=lambda b: uuid.UUID(bytes=b),
    to_json=lambda u: str(u),
    from_json=lambda u: uuid.UUID(u),
  )


def uuid_fk_field(
  reference_table: str,
  reference_column: str = "id",
  primary: bool = False,
  nullable: bool = False,
  on_delete: ForeignKeyAction = "CASCADE",
):
  return Field(
    uuid.UUID,
    sql_type=ColumnType.BLOB,
    primary_key=primary,
    nullable=False if primary else nullable,
    foreign_key=ForeignKey(reference_table, reference_column, on_delete=on_delete),
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


def enum_field(enum: type[Enum], sql_type: ColumnType, nullable: bool = True):
  return Field(
    enum,
    sql_type,
    nullable=nullable,
    to_sql=lambda x: x.value,
    from_sql=lambda x: enum(x),
    to_json=lambda x: x.value if isinstance(x, enum) else x,
    from_json=lambda x: enum(x),
  )


def json_field(python_json: type[T], nullable: bool = True):
  return Field(
    python_json,
    ColumnType.TEXT,
    nullable=nullable,
    to_sql=lambda x: json.dumps(x),
    from_sql=lambda x: json.loads(x),
  )


def jsonb_field(python_json: type[T], nullable: bool = True):
  return Field(
    python_json,
    ColumnType.BLOB,
    nullable=nullable,
    to_sql=lambda x: json.dumps(x),
    from_sql=lambda x: json.loads(x),
  )


def uuid_list_junction_model(parent_model: type[Table], column_name: str):
  parent_table = parent_model.table_name()
  junction_table_name = f"{parent_table}_{column_name}"

  class Junction(Table):
    _table_name = junction_table_name
    _without_rowid = True
    parent_id = uuid_fk_field(parent_table, "id", primary=True)
    value = uuid_field(True, False)

    _indexes = (Index(("value",), name=f"ix_{junction_table_name}_value"),)

  Junction.__name__ = f"{junction_table_name.title().replace('_', '')}Table"
  return Junction
