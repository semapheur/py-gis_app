from datetime import datetime
from pathlib import Path
from typing import Optional, Union, cast

from src.const import INDEX_DB
from src.path_utils import verify_dir
from src.spatialite import DATETIME_FIELD, ColumnType, Field, Model, SpatialDatabase


class CatalogTable(Model):
  table_name = "catalog"
  id = Field(int, primary_key=True)
  path = Field(
    Path,
    sql_type=ColumnType.TEXT,
    nullable=False,
    unique=True,
    to_sql=lambda x: str(x),
    to_python=lambda x: Path(x),
    to_json=lambda x: str(x),
  )
  name = Field(str, nullable=False, unique=True)
  last_indexed = DATETIME_FIELD


def insert_catalog(
  db: SpatialDatabase,
  path: Path,
  name: str,
):
  if db.conn is None:
    raise RuntimeError("Database not connected")

  cursor = db.conn.cursor()

  cursor.execute("SELECT id FROM catalog WHERE name = ?", (name,))
  row = cursor.fetchone()
  if not row:
    raise ValueError(f"Catalog name already exists: {name}")

  cursor.execute("SELECT id FROM catalog WHERE path = ?", (path,))
  row = cursor.fetchone()
  if not row:
    raise ValueError(f"Catalog path already exists: {path}")

  now = datetime.now().isoformat(timespec="seconds")
  cursor.execute(
    """
    INSERT INTO catalog (path, name, last_indexed)
    VALUES (?, ?, ?)
  """,
    (str(path.resolve()), name, now),
  )
  db.conn.commit()


def update_catalog(
  db: SpatialDatabase,
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

  with SpatialDatabase(INDEX_DB) as db:
    db.create_table(CatalogTable)
    insert_catalog(db, path, name)


def get_catalogs() -> dict[int, dict[str, str]]:
  with SpatialDatabase(INDEX_DB) as db:
    catalogs = db.select_records(CatalogTable, "*")

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

  with SpatialDatabase(INDEX_DB) as db:
    update_catalog(db, id, new_path, new_name)
