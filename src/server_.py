import json
import logging
import mimetypes
import os
import re
import uuid
from http.server import SimpleHTTPRequestHandler
from io import BufferedReader
from pathlib import Path
from typing import Any, Callable, TypedDict, TypeVar

from src.bootstrap import get_settings
from src.hashing import decode_sha256_from_b64
from src.index.catalog import (
  InsertCatalog,
  UpdateCatalog,
  get_catalog_edit_data,
  get_catalog_index_data,
  insert_catalog,
  update_catalog,
  validate_catalog_dir,
)
from src.index.images import ImageQuery, get_image_info, index_images, search_images
from src.index.radiometric import get_radiometric_parameters
from src.models.annotation_schema import (
  InsertSchema,
  UpdateSchema,
  get_schema_data,
  get_schema_data_options,
  insert_schema,
  update_schema,
)
from src.models.areas import (
  AreaDelete,
  AreaId,
  AreaUpdate,
  delete_areas,
  get_area,
  get_areas,
  update_area,
)
from src.models.attributes import (
  ATTRIBUTE_TABLES,
  InsertAttribute,
  UpdateAttribute,
  get_attribute_data,
  get_attribute_options,
  get_attribute_tables,
  insert_attribute,
  update_attribute,
)
from src.models.equipment_annotation import (
  AnnotationUpdate,
  ConvertAnnotation,
  GhostSearch,
  convert_annotation,
  delete_annotations,
  get_annotation_ghosts,
  get_annotations_by_image,
  update_annotations,
)
from src.models.equipment_list import get_equipment, search_equipment, update_equipment
from src.models.security import (
  InsertSecurity,
  UpdateSecurity,
  get_security_data,
  insert_sequrity,
  update_security,
)
from src.models.update import TableUpdate
from src.msgpack import decode_msgpack, encode_msgpack

P = TypeVar("P")
R = TypeVar("R")

app_settings = get_settings()

logger = logging.getLogger(__name__)


class ApiError(Exception):
  def __init__(self, status: int, message: str):
    super().__init__(message)
    self.status = status
    self.message = message


PARAM_REGEX = re.compile(r"\{(\w+)\}")


def compile_pattern(path: str) -> re.Pattern:
  regex = PARAM_REGEX.sub(r"(?P<\1>[^/]+)", path)
  return re.compile(f"^{regex}$")


def api(method: str, path: str, *, stream: bool = False):

  def decorator(fn: Callable) -> Callable:
    fn._route = (method.upper(), path, stream)
    return fn

  return decorator


class ApiRouterMeta(type):
  def __new__(mcs, name, bases, ns):
    cls = super().__new__(mcs, name, bases, ns)

    exact: dict[str, dict[str, tuple]] = {"GET": {}, "POST": {}}
    patterns: dict[str, list[tuple]] = {"GET": [], "POST": []}

    for base in bases:
      be = getattr(base, "_exact_routes", None)
      bp = getattr(base, "_pattern_routes", None)

      if be:
        for m in exact:
          exact[m].update(be.get(m, {}))

      if bp:
        for m in patterns:
          patterns[m].extend(bp.get(m, []))

    for attr in ns.values():
      route = getattr(attr, "_route", None)
      if route is None:
        continue

      method, path, stream = route
      if "{" in path:
        patterns[method].append((compile_pattern(path), attr, stream))
      else:
        exact[method][path] = (attr, stream)

    cls._exact_routes = exact
    cls._pattern_routes = patterns
    return cls


class ApiHandler(SimpleHTTPRequestHandler, metaclass=ApiRouterMeta):
  def translate_path(self, path: str) -> str:
    if path.startswith("/api"):
      return path

    relative_path = path.lstrip("/")
    full_path = app_settings.STATIC_DIR / relative_path

    if full_path.is_dir():
      return str(full_path)

    return super().translate_path(path)

  def _serve_static(self):
    path = self.translate_path(self.path)
    if not os.path.exists(path):
      self.send_error(404, "File not found")
      return

    file_size = os.path.getsize(path)
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"

    range_header = self.headers.get("Range")

    if range_header:
      units, rng = range_header.strip().split("=")
      start_str, end_str = rng.split("-")

      start = int(start_str)
      end = int(end_str) if end_str else file_size - 1
      end = min(end, file_size - 1)

      self.send_response(206)
      self._send_cors_headers()
      self.send_header("Content-Type", content_type)
      self.send_header("Accept-Ranges", "bytes")
      self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
      self.send_header("Content-Lengt", str(end - start + 1))
      self.end_headers()

      with open(path, "rb") as f:
        f.seek(start)
        self._stream_file(f, end - start + 1)

  def _send_cors_headers(self):
    origin = self.headers.get("Origin")
    if origin:
      self.send_header("Access-Controll-Allow-Origin", origin)
      self.send_header("Vary", "Origin")

    self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "Range")
    self.send_header(
      "Access-Control-Expose-Headers",
      "Content-Length, Content-Range, Accept-Ranges, Content-Encoding",
    )

  def _stream_file(self, file: BufferedReader, length: int):
    chunk_size = 256 * 1024
    remaining = length

    while remaining > 0:
      chunk = file.read(min(chunk_size, remaining))
      if not chunk:
        break

      try:
        self.wfile.write(chunk)
      except ConnectionResetError:
        break
      remaining -= len(chunk)

  def _dispatch(self, method: str) -> bool:
    path = self.path.split("?", 1)[0]

    hit = self._exact_routes[method].get(path)
    if hit:
      fn, stream = hit
      self._invoke(fn, stream, {})
      return True

    for regex, fn, stream in self._pattern_routes[method]:
      m = regex.match(path)
      if m:
        self._invoke(fn, stream, m.groupdict())
        return True

    return False

  def _invoke(self, fn: Callable, stream: bool, path_params: dict[str, str]):
    if stream:
      self._invoke_stream(fn, path_params)
    elif self.command == "POST":
      self._invoke_post(fn, path_params)
    else:
      self._invoke_get(fn, path_params)

  def _invoke_get(self, fn: Callable, path_params: dict[str, str]):
    try:
      result = fn(self, **path_params)
      self._api_response(result)
    except ApiError as e:
      self._error_response(e.status, e.message)
    except Exception as e:
      logger.exception("Error handle %s", self.path)
      self._error_response(500, f"Sever error: {e}")

  def _invoke_post(self, fn: Callable, path_params: dict[str, str]):
    try:
      content_length = int(self.headers.get("Content-Length", 0))
      body = self.rfile.read(content_length)
      payload = decode_msgpack(body)
    except Exception as e:
      self._error_response(400, f"Bad request: {e}")
      return

    try:
      result = fn(self, payload, **path_params)
      self._api_response(result)
    except ApiError as e:
      self._error_response(e.status, e.message)
    except Exception as e:
      logger.exception("Error handling %s", self.path)
      self._error_response(500, f"Server error: {e}")

  def _invoke_stream(self, fn: Callable, path_params: dict[str, str]):
    try:
      content_length = int(self.headers.get("Content-Length", 0))
      body = self.rfile.read(content_length)
      payload = decode_msgpack(body)
    except Exception as e:
      self._error_response(400, f"Bad request: {e}")
      return

    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("X-Accel-Buffering", "no")
    self.end_headers()

    def send_event(event: str, data: dict):
      chunk = f"event: {event}\ndata: {json.dumps(data)}\n\n"
      self.wfile.write(chunk.encode("utf-8"))
      self.wfile.flush()

    try:
      fn(self, payload, send_event, **path_params)
      send_event("done", {"message": "OK"})
    except Exception as e:
      logger.exception("Error in stream handler")
      send_event("error", {"message": str(e)})

  def _api_response(self, obj: Any):
    payload = encode_msgpack(obj)
    self.send_response(200)
    self.send_header("Content-Type", "application/msgpack")
    self.send_header("Content-Length", str(len(payload)))
    self.end_headers()
    self.wfile.write(payload)

  def _error_response(self, status: int, message: str):
    payload = encode_msgpack({"detail": message})
    self.send_response(status)
    self.send_header("Content-Type", "application/msgpack")
    self.send_header("Content-Length", str(len(payload)))
    self.end_headers()
    self.wfile.write(payload)

  def do_GET(self):
    if self._dispatch("GET"):
      return
    if self.path.startswith("/api"):
      self.send_error(404, "Unknown GET endpoint")
      return
    self._serve_static()

  def do_POST(self):
    if self._dispatch("POST"):
      return

    self.send_error(404, "Unkown POST endpoint")

  def do_OPTIONS(self):
    self.send_response(204)
    self._send_cors_headers()
    self.end_headers()


class Handler(ApiHandler):
  @api("GET", "/api/attribute-tables")
  def _get_attribute_tables(self):
    return {"tables": get_attribute_tables()}

  @api("GET", "/api/schema-data-options")
  def _get_schema_data_options(self):
    return {"options": get_schema_data_options()}

  @api("GET", "/api/get-equipment")
  def _get_equipment(self):
    return get_equipment()

  @api("GET", "/api/get-areas")
  def _get_areas(self):
    return get_areas()

  @api("GET", "/api/get-catalogs-index")
  def _get_catalogs_index(self):
    return {"catalogs": get_catalog_index_data()}

  @api("GET", "/api/get-catalogs-edit")
  def _get_catalogs_edit(self):
    return {"catalogs": get_catalog_edit_data()}

  @api("GET", "/api/get-annotations/{image_id}")
  def _get_annotations(self, image_id: str):
    image_hash = decode_sha256_from_b64(image_id)
    return get_annotations_by_image(image_hash)

  @api("GET", "/api/attribute-data/schema")
  def _get_schema_data(self):
    return {"data": get_schema_data()}

  @api("GET", "/api/attribute-data/{table}")
  def _get_attribute_data(self, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid GET endpoint")
    return {"data": get_attribute_data(table)}

  @api("GET", "/api/get-attributes/{table}")
  def _get_attributes(self, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid GET endpoint")
    return {"options": get_attribute_options(table)}

  @api("POST", "/api/search-images")
  def _post_query_images(self, payload: ImageQuery):
    return search_images(payload)

  @api("POST", "/api/image-info")
  def _post_image_info(self, payload: dict):
    image_hash = decode_sha256_from_b64(payload["id"])
    return get_image_info(image_hash)

  @api("POST", "/api/update-equipment")
  def _post_update_equipment(self, payload: TableUpdate):
    return update_equipment(payload)

  @api("POST", "/api/insert-attribute/schema")
  def _post_insert_schema(self, payload: InsertSchema):
    return {"inserted_row": insert_schema(payload)}

  @api("POST", "/api/insert-attribute/{table}")
  def _post_insert_attribute(self, payload: InsertAttribute, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid POST endpoint")
    return {"inserted_row": insert_attribute(table, payload)}

  @api("POST", "/api/update-attribute/schema")
  def _post_update_schema(self, payload: UpdateSchema):
    return update_schema(payload)

  @api("POST", "/api/update-attribute/{table}")
  def _post_update_attribute(self, payload: UpdateAttribute, table: str):
    if table not in ATTRIBUTE_TABLES:
      raise ApiError(404, "Invalid POST endpoint")
    return update_attribute(table, payload)

  @api("POST", "/api/update-area")
  def _post_update_area(self, payload: AreaUpdate):
    name = update_area(payload)
    if name is not None:
      raise ApiError(409, f"Area with '{name}' already exist!")

  @api("POST", "/api/validate-catalog-dir")
  def _post_validate_catalog_dir(self, payload: dict):
    input_path = Path(payload["path"])
    try:
      validate_catalog_dir(input_path)
    except FileNotFoundError as e:
      raise ApiError(400, str(e))
    except ValueError as e:
      raise ApiError(409, str(e))
    return {"valid": True}

  @api("POST", "/api/index-catalog", stream=True)
  def _post_index_catalog(self, payload: dict, send_event: Callable[[str, dict], None]):
    catalog_id = uuid.UUID(payload["id"])

    def on_progress(current: int, total: int, filename: str):
      send_event(
        "progress",
        {
          "current": current,
          "total": total,
          "filename": filename,
          "percent": round(current / total * 100) if total else 0,
        },
      )

    index_images(catalog_id, progress_callback=on_progress)
