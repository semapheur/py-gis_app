from datetime import datetime
from pathlib import Path
from typing import Optional, Union, cast

from src.const import INDEX_DB
from src.path_utils import verify_dir
from src.spatialite import (
  Field,
  Model,
  SqliteDatabase,
  datetime_field,
  path_field,
)
from src.timeutils import datetime_to_unix


class CatalogTable(Model):
  _table_name = "catalog"
  id = Field(int, primary_key=True)
  path = path_field(False, True)
  name = Field(str, nullable=False, unique=True)
  last_indexed = datetime_field(True)


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


def update_catalog(
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


def add_calatog(path: Path, name: str):
  verify_dir(path)

  with SqliteDatabase(INDEX_DB) as db:
    db.create_table(CatalogTable)
    insert_catalog(db, path, name)


def get_catalogs() -> dict[int, dict[str, str]]:
  with SqliteDatabase(INDEX_DB) as db:
    catalogs = db.select_records(CatalogTable, columns="*")

  result: dict[int, dict[str, str]] = {}
  for row in catalogs:
    result[row["id"]] = {
      "name": row["name"],
      "path": str(row["path"].resolve()),
      "last_indexed": cast(datetime, row["last_indexed"]).isoformat(timespec="seconds"),
    }

  return result


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

  with SqliteDatabase(INDEX_DB) as db:
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
