import re
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable, Optional, Union

GEOMETRIES = ("point", "polygon", "multipolygon")

WKT_PATTERN = re.compile(r"^(?:SRID=\d+;)?(POINT|POLYGON|MULTIPOLYGON)", re.IGNORECASE)
AUDIT_COLUMNS = ("modifiedByUserId", "modifiedAtTimestamp")


@dataclass
class Upsert:
  type: str
  data: dict[str, Any]
  is_new: bool = False
  inherit_created_from: Optional[str] = None


@dataclass
class Delete:
  type: str
  geometry: str
  ids: list[uuid.UUID]


Mutation = Union[Upsert, Delete]


def parse_mutations(raw: Any) -> list[Mutation]:
  if not isinstance(raw, list):
    raise TypeError("Payload must be a list of mutations")
  return [_parse_mutation(m) for m in raw]


def _parse_mutation(raw: Any) -> Mutation:
  if not isinstance(raw, dict):
    raise TypeError("Mutation must be an object")

  annotation_type = raw.get("type")
  if annotation_type not in SPECS:
    raise ValueError(f"Unsupported annotation type: {annotation_type}")

  op = raw.get("op")

  if op == "upsert":
    data = raw.get("data")
    if not isinstance(data, dict):
      raise ValidationError("Missing annotation data")

    inherit = raw.get("inheritCreatedFrom")
    if inherit is not None and inherit not in GEOMETRIES:
      raise ValidationError(f"Invalid inheritCreatedFrom: {inherit}")

    return Upsert(
      type=annotation_type,
      data=data,
      is_new=bool(raw.get("isNew", False)),
      inherit_created_from=inherit,
    )

  if op == "delete":
    geometry = raw.get("geometry")
    ids = raw.get("ids")
    if geometry not in GEOMETRIES:
      raise ValidationError(f"Invalid geometry: {geometry}")
    if not isinstance(ids, list):
      raise ValidationError("ids must be a list")
    try:
      return Delete(annotation_type, geometry, [uuid.UUID(str(i)) for i in ids])
    except ValueError:
      raise ValidationError("ids must be UUIDs")

  raise ValidationError(f"Invalid op: {op}")
