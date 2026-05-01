from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import (
  Any,
  Mapping,
  Optional,
  Sequence,
  Union,
)

from src.sqlite.query_builder import OnConflict, Query
from src.sqlite.table import SqliteValue, Table


class SqliteDatabase:
  def __init__(self, db_path: Path, spatial: bool = False):
    self.db_path = db_path
    self.spatial = spatial
    self.conn = None

  def __enter__(self):
    if not self.db_path.parent.exists():
      raise FileNotFoundError(f"Directory does not exist: {self.db_path.parent}")

    if self.db_path.suffix.lower() not in {".db", ".sqlite"}:
      raise ValueError(f"Invalid db path: {self.db_path}")

    self.conn = sqlite3.connect(self.db_path)

    if self.spatial:
      self.conn.enable_load_extension(True)
      self.conn.load_extension(os.environ["SPATIALITE"])
      self._ensure_spatial_metadata()

    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if not self.conn:
      return False

    try:
      if exc_type is None:
        self.conn.commit()
      else:
        self.conn.rollback()
    finally:
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

  @contextmanager
  def transaction(self):
    self._check_connection()
    cursor = self.conn.cursor()
    try:
      cursor.execute("BEGIN TRANSACTION")
      yield cursor
      cursor.execute("COMMIT")
    except Exception:
      cursor.execute("ROLLBACK")
      raise

  def create_table(self, table: type[Table]) -> bool:
    if self.conn is None:
      raise RuntimeError("Database not connected")

    if table_exists(self.conn, table._table_name):
      return False

    cursor = self.conn.cursor()
    cursor.execute(table.create_table_sql())

    for sql in table.add_geometry_sql():
      cursor.execute(sql)

    return True

  def create_fts_table(self, table: type[Table], columns: Sequence[str]):
    self._check_connection()

    table_name = table._table_name
    fts_name = f"{table_name}_fts"

    if table_exists(self.conn, fts_name):
      return

    fts_columns = ",".join(columns)
    fts_options = f"{fts_columns},content='{table_name}'"

    create_sql = (
      f"""CREATE VIRTUAL TABLE IF NOT EXISTS {fts_name} USING fts5({fts_options})"""
    )

    new = ",".join([f"new.{c}" for c in columns])

    trigger_after_insert = f"""
    CREATE TRIGGER {table_name}_ai AFTER INSERT ON {table_name}
    BEGIN
      INSERT INTO {fts_name}(rowid,{fts_columns})
      VALUES (new.rowid,{new});
    END
    """

    update_parts = [f"{c} = new.{c}" for c in columns]
    trigger_after_update = f"""CREATE TRIGGER {table_name}_au AFTER UPDATE ON {table_name}
    BEGIN
      UPDATE {fts_name}
      SET {",".join(update_parts)}
      WHERE rowid = new.rowid;
    END
    """

    trigger_after_delete = f"""
      CREATE TRIGGER {table_name}_ad AFTER DELETE ON {table_name}
      BEGIN
        DELETE FROM {fts_name}
        WHERE rowid = old.rowid;
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
    models: Sequence[Table],
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

  def select_records(
    self, table: type[Table], query: Query, to_json: bool = False
  ) -> list[dict[str, SqliteValue]]:
    columns = query.columns
    sql, params = query.build()
    cursor = self.conn.cursor()
    rows = cursor.execute(sql, params).fetchall()

    results: list[dict[str, SqliteValue]] = []
    for row in rows:
      result_row = {}
      for i, (name, alias) in enumerate(columns):
        col = alias or name
        field = table._fields.get(col)
        if field is None:
          result_row[col] = row[i]
          continue

        if field.geometry_type is None:
          value = field.deserialize_from_sql(row[i])
        else:
          geo_regex = re.compile("^As(GeoJSON|Text)")
          match = geo_regex.search(name)
          geo_format = "" if match is None else match.group()

          value = json.loads(row[i]) if geo_format == "AsGeoJSON" else row[i]

        result_row[col] = field.serialize_to_json(value) if to_json else value

      results.append(result_row)

    return results

  def delete_by_ids(self, table: type[Table], ids: list[Any]) -> int:
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

  def convert_geometry(
    self,
    source_table: type[Table],
    target_table: type[Table],
    id: Any,
    geometry_wkt: str,
    srid: int = 4326,
  ):

    self._check_connection()
    cursor = self.conn.cursor()

    geometry_columns = source_table.geometry_names()
    if len(geometry_columns) != 1:
      raise ValueError(
        f"Source table {source_table.__name__} must have a single geometry column. Found ${len(geometry_column)}"
      )

    geometry_column = geometry_columns[0]

    source_columns = source_table.column_names(True)
    target_columns = target_table.column_names(True)

    common_columns = set(source_columns).intersection(target_columns)
    if not common_columns:
      raise ValueError(
        f"No common columns between {source_table} and {target_table} "
        f"(excluding geometry). "
        f"Source columns: {sorted(source_columns)}, "
        f"Target columns: {sorted(target_columns)}"
      )

    self._validate_field_compatibility(source_table, target_table, common_columns)

    column_list = ", ".join(sorted(common_columns))

    params = {"id": id, "geometry": geometry_wkt, "srid": srid}
    cursor.execute(
      f"""
      INSERT INTO '{target_table._table_name}'({column_list}, '{geometry_column}')
      SELECT {column_list}, ST_GeomFromText(:geometry, :srid)
      FROM '{source_table._table_name}'
      WHERE id = :id
    """,
      params,
    )

    if cursor.rowcount == 0:
      raise ValueError(f"Failed to insert into {target_table}")

    cursor.execute(
      f"DELETE FROM '{source_table._table_name}' WHERE id = :id", {"id": id}
    )

  def _validate_field_compatibility(
    self, source_model: type[Table], target_model: type[Table], common_columns: set[str]
  ):

    issues: list[str] = []
    for col in common_columns:
      source_field = source_model._fields[col]
      target_field = target_model._fields[col]

      if source_field.sql_type != target_field.sql_type:
        issues.append(
          f"Column '{col}': SQL type mismatch "
          f"({source_field.sql_type} -> {target_field.sql_type})"
        )

      if source_field.nullable and not target_field.nullable:
        issues.append(f"Column '{col}': Source is nullable but target is NOT NULL")

      if source_field.primary_key != target_field.primary_key:
        issues.append(
          f"Column '{col}': Primary key mismatch "
          f"(source: {source_field.primary_key}, target: {target_field.primary_key})"
        )

    if issues:
      raise ValueError(
        f"Field compatibility issues between {source_model.__name__} "
        f"and {target_model.__name__}:\n"
        + "\n".join(f"  - {issue}" for issue in issues)
      )


def table_exists(db: sqlite3.Connection, table_name: str) -> bool:
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
