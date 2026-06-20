import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, TypedDict, Union

from src.bootstrap import get_settings
from src.models.update import TableUpdate, update_table
from src.path_utils import verify_dir
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import SelectQuery, UpdateQuery
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


def validate_catalog_dir(path: Path, check_db_presence: bool = False):

  if not path.is_dir():
    raise FileNotFoundError(f"Invalid directory path: {path}")

  if not check_db_presence:
    return

  query = (
    SelectQuery()
    .select("id")
    .from_(CatalogTable._table_name)
    .where("path = ?", str(path))
  )
  with SqliteDatabase(app_settings.INDEX_DB) as db:
    result = db.select_model_records(CatalogTable, query, True)

  if result:
    raise ValueError(f"Catalog path already exists: {str(path)}")


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


def parse_id_name_path_record(row: tuple[bytes, str, str]):
  return {
    "id": str(uuid.UUID(bytes=row[0])),
    "path": row[1],
    "name": row[2],
  }


class InsertCatalog(TypedDict):
  path: str
  name: str


def insert_catalog(payload: InsertCatalog):
  path = Path(payload["path"])
  verify_dir(path)

  model = CatalogTable.from_dict(
    {"id": uuid.uuid4(), "path": path, "name": payload["name"], "last_indexed": None}
  )

  returning_sql = "id, path, name"

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    result = db.insert_models([model], returning=returning_sql)

  return parse_id_name_path_record(result[0])


class UpdateCatalog(TypedDict):
  id: str
  path: str
  name: str


def update_catalog(payload: UpdateCatalog):
  path = Path(payload["path"])
  verify_dir(path)

  model = CatalogTable.from_dict(
    {
      "id": uuid.UUID(payload["id"]),
      "path": path,
      "name": payload["name"],
    }
  )

  update_query = UpdateQuery().set_excluded("path", "name")

  returning_sql = "id, path, name"

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    result = db.insert_models([model], "id", update_query, returning_sql)

  return parse_id_name_path_record(result[0])


def get_catalog_edit_data():
  columns = ("id", "path", "name")
  query = SelectQuery().select(*columns).from_(CatalogTable._table_name)

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    return db.select_model_records(CatalogTable, query, True)


def get_catalog_index_data():
  from src.index.images import ImageIndexTable

  table_c = CatalogTable._table_name
  table_c_as = table_c[0]
  table_i = ImageIndexTable._table_name
  table_i_as = table_i[0]
  columns = (
    f"{table_c_as}.id AS id",
    f"{table_c_as}.path AS path",
    f"{table_c_as}.name AS name",
    f"COUNT({table_i_as}.catalog) AS indexed_images",
    f"{table_c_as}.last_indexed AS last_indexed",
  )

  query = (
    SelectQuery()
    .select(*columns)
    .from_(f"{table_c} {table_c_as}")
    .join(
      f"{table_i} {table_i_as}",
      on=f"{table_i_as}.catalog = {table_c_as}.id",
      join_type="LEFT",
    )
    .group_by(f"{table_c_as}.id")
  )

  with SqliteDatabase(app_settings.INDEX_DB) as db:
    return db.select_model_records(CatalogTable, query, True)


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
    update_catalog_entry(db, id, new_path, new_name)


def update_index_time(db: SqliteDatabase, id: uuid.UUID, index_time: datetime):
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
    (timestamp, id.bytes),
  )
  db.conn.commit()
