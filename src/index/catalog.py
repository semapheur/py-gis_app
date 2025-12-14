from datetime import datetime
from pathlib import Path
from typing import cast

from src.spatialite import Field, Model, SpatialDatabase


class CatalogTable(Model):
  table_name = "catalog"
  id = Field(int, primary_key=True)
  path = Field(
    Path,
    sql_type=str,
    nullable=False,
    unique=True,
    to_sql=lambda x: str(x),
    to_python=lambda x: Path(x),
  )
  name = Field(str, nullable=False, unique=True)
  last_indexed = Field(
    datetime,
    str,
    nullable=False,
    to_sql=lambda x: datetime.isoformat(x, sep=" ", timespec="seconds"),
    to_python=lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S"),
  )


def upsert_catalog(db: SpatialDatabase, path: str, name: str) -> int:
  if db.conn is None:
    raise RuntimeError("Database not connected")

  cursor = db.conn.cursor()

  cursor.execute("SELECT id FROM catalog WHERE name = ?", (name,))
  row = cursor.fetchone()
  if row is not None:
    raise ValueError(f"Catalog name already exists: {name}")

  cursor.execute("SELECT id FROM catalog WHERE path = ?", (path,))
  row = cursor.fetchone()
  if row is not None:
    return row[0]

  now = datetime.now().isoformat(timespec="seconds")
  cursor.execute(
    """
    INSERT INTO catalog (path, name, last_indexed)
    VALUES (?, ?, ?)
    RETURNING id
  """,
    (path, name, now),
  )

  new_id = cast(int, cursor.fetchone()[0])
  db.conn.commit()
  return new_id
