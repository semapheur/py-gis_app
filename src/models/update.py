import uuid
from pathlib import Path
from typing import Optional, TypedDict, cast

from src.bootstrap import get_settings
from src.sqlite.connect import SqliteDatabase
from src.sqlite.query_builder import OnConflict
from src.sqlite.table import SqliteValue, Table

app_settings = get_settings()


class TableUpdate(TypedDict):
  create: list[dict[str, SqliteValue]]
  update: list[dict[str, SqliteValue]]
  delete: list[str]


class IdMap(TypedDict):
  client_id: str
  server_id: str


class CreatedRows(TypedDict):
  created: list[IdMap]


def resolve_ids(records: list[dict]) -> list[IdMap]:
  created: list[IdMap] = []

  for record in records:
    record_id = cast(Optional[str], record.get("id"))
    if record_id is None:
      raise ValueError(f"Missing 'id' field in create record: {record}")
    if not record_id.startswith("temp://"):
      continue

    new_id = uuid.uuid4()
    record["id"] = str(new_id)
    created.append(IdMap(client_id=record_id, server_id=str(new_id)))

  return created


def update_table(
  db_path: Path, model: type[Table], payload: TableUpdate, update_sql: str
) -> CreatedRows:

  created_ids = resolve_ids(payload["create"])
  create_models = [model.from_dict(record, json=True) for record in payload["create"]]
  update_models = [model.from_dict(record, json=True) for record in payload["update"]]
  delete_ids = [uuid.UUID(u) for u in payload["delete"]]

  with SqliteDatabase(db_path) as db:
    if update_models:
      db.insert_models(update_models, OnConflict(index="id", action=update_sql))

    if delete_ids:
      db.delete_by_ids(model, delete_ids)

    if create_models:
      db.insert_models(create_models)

  return CreatedRows(created=created_ids)
