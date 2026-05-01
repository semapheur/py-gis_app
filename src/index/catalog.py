from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from src.bootstrap import get_settings
from src.models.update import TableUpdate, update_table
from src.path_utils import verify_dir
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import Query
from src.sqlite.table import (
  Field,
  Table,
  datetime_field,
  path_field,
  uuid_field,
)
from src.timeutils import datetime_to_unix

app_settings = get_settings()


class CatalogTable(Table):
  _table_name = "catalog"
  id = uuid_field(True, False)
  path = path_field(False, True)
  name = Field(str, nullable=False, unique=True)
  last_indexed = datetime_field(True)


def create_catalog_table():
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    db.create_table(CatalogTable)


def validate_catalog_dir(path: Path):

  if not path.is_dir():
    raise FileNotFoundError(f"Invalid directory path: {path}")

  query = (
    Query().select("id").from_(CatalogTable._table_name).where("path = ?", str(path))
  )
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    result = db.select_records(CatalogTable, query, True)

  if result:
    raise ValueError(f"Catalog path already exists: {str(path)}")


def insert_catalog(
  db: SqliteDatabase,
  path: Path,
  name: str,
):
  if db.conn is None:
    raise RuntimeError("Database not connected")

  cursor = db.conn.cursor()
  full_path = str(path.resolve())

  cursor.execute("SELECT id FROM catalog WHERE name = ?", (name,))
  row = cursor.fetchone()
  if row:
    raise ValueError(f"Catalog name already exists: {name}")

  cursor.execute("SELECT id FROM catalog WHERE path = ?", (full_path,))
  row = cursor.fetchone()
  if row:
    raise ValueError(f"Catalog path already exists: {path}")

  cursor.execute(
    """
    INSERT INTO catalog (path, name)
    VALUES (?, ?)
  """,
    (full_path, name),
  )
  db.conn.commit()


def update_catalog_entry(
  db: SqliteDatabase,
  id: int,
  new_path: Optional[Path] = None,
  new_name: Optional[str] = None,
):
  if db.conn is None:
    raise RuntimeError("Database not connected")

  cursor = db.conn.cursor()

  sql = """SELECT COALESCE(
    (SELECT id FROM catalog WHERE id = ?),
    (SELECT MAX(id) FROM catalog)
  ) AS result
  """
  cursor.execute(sql, (id,))
  rows = cursor.fetchone()
  if not rows:
    raise ValueError("No catalogs registered")

  check_id = rows[0]

  if id != check_id:
    raise ValueError(
      f"No catalog found with id {id}. Valid ids are in the range 1-{check_id}"
    )

  set_parts: list[str] = []
  params: dict[str, Union[int, str]] = {"id": id}
  if new_path is not None:
    set_parts.append("path = :new_path")
    params["new_path"] = str(new_path.resolve())

  if new_name is not None:
    set_parts.append("name = :new_name")
    params["new_name"] = new_name

  set_sql = ", ".join(set_parts)
  sql = f"UPDATE catalog SET {set_sql} WHERE id = :id"
  cursor.execute(sql, params)
  db.conn.commit()


def update_catalogs(payload: TableUpdate):
  records = [*payload["create"], *payload["update"]]
  for record in records:
    path = record.get("path")
    if path is None:
      raise ValueError(f"Catalog record is missing 'path' field: {record}")

    if not isinstance(path, str):
      raise ValueError(f"Catalog 'path' field must be string, got: {path}")

    verify_dir(Path(path))

  update_sql = """UPDATE SET
    path = excluded.path,
    name = excluded.name
  """

  return update_table(app_settings.INDEX_DB, CatalogTable, payload, update_sql)


def add_calatog(path: Path, name: str):
  verify_dir(path)

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    insert_catalog(db, path, name)


def get_catalogs():
  columns = CatalogTable.column_sql()
  query = Query().select(*columns).from_(CatalogTable._table_name)

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    return db.select_records(CatalogTable, query, True)


def edit_catalog(
  id: int,
  new_path: Optional[Path] = None,
  new_name: Optional[str] = None,
):
  if id < 1:
    raise ValueError(f"id must be a positive integer (>= 1), got: {id}")

  if new_name is None and new_path is None:
    raise ValueError("Nothing to edit")

  if new_path is not None:
    verify_dir(new_path)

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    update_catalog(db, id, new_path, new_name)


def update_index_time(db: SqliteDatabase, id: int, index_time: datetime):
  timestamp = datetime_to_unix(index_time)

  if db.conn is None:
    raise RuntimeError("Database not connected")

  cursor = db.conn.cursor()

  cursor.execute(
    """
    UPDATE catalog
    SET last_indexed = ?
    WHERE id = ?
  """,
    (timestamp, id),
  )
  db.conn.commit()
