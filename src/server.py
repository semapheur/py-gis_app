import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler
from io import BufferedReader
from typing import Any, Callable, TypedDict, TypeVar

from src.annotations.models import AnnotationUpdate, get_annotations, update_annotation
from src.attributes.models import (
  ATTRIBUTE_TABLES,
  AttributeUpdate,
  get_attribute_data,
  get_attribute_schema,
  get_attribute_tables,
  search_equipment,
  update_attributes,
)
from src.const import STATIC_DIR
from src.hashing import decode_sha256_from_b64
from src.index.images import get_image_info, get_images_by_intersection
from src.index.radiometric import get_radiometric_parameters

P = TypeVar("P")
R = TypeVar("R")


class Handler(SimpleHTTPRequestHandler):
  def translate_path(self, path: str) -> str:
    if path.startswith("/api"):
      return path

    rel = path.lstrip("/")
    full = STATIC_DIR / rel

    if full.is_dir():
      return str(STATIC_DIR / "index.html")

    if full.exists():
      return str(full)

    return super().translate_path(path)

  def do_GET(self):
    if self.path == "/api/attribute-tables":
      self._get_attribute_tables()
      return

    prefix = "/api/attribute-schema/"
    if self.path.startswith(prefix):
      table = self.path[len(prefix) :]
      self._get_attribute_schema(table)
      return

    prefix = "/api/attribute-data/"
    if self.path.startswith(prefix):
      table = self.path[len(prefix) :]
      self._get_attribute_data(table)
      return

    prefix = "/api/get-attributes/"
    if self.path.startswith(prefix):
      table = self.path[len(prefix) :]
      self._get_attributes(table)
      return

    prefix = "/api/get-annotations/"
    if self.path.startswith(prefix):
      image_id = self.path[len(prefix) :]
      self._get_annotations(image_id)
      return

    if self.path.startswith("/api"):
      self.send_error(404, "Unknown GET endpoint")
      return

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
      self.send_header("Content-Length", str(end - start + 1))
      self.end_headers()

      with open(path, "rb") as f:
        f.seek(start)
        self._stream_file(f, end - start + 1)

    else:
      self.send_response(200)
      self.send_header("Content-Type", content_type)
      self.send_header("Content-Length", str(file_size))
      self.send_header("Accept-Ranges", "bytes")
      self._send_cors_headers()
      self.end_headers()

      with open(path, "rb") as f:
        self._stream_file(f, file_size)

  def do_POST(self):
    if self.path == "/api/search-images":
      self._post_query_images()
      return

    if self.path == "/api/image-info":
      self._post_image_info()
      return

    if self.path == "/api/radiometric-params":
      self._post_parametric_params()
      return

    if self.path == "/api/search-equipment":
      self._post_search_equipment()
      return

    prefix = "/api/update-attributes/"
    if self.path.startswith(prefix):
      table = self.path[len(prefix) :]
      self._post_update_attributes(table)
      return

    if self.path == "/api/update-annotation":
      self._post_update_annotation()
      return

    self.send_error(404, "Unknown POST endpoint")

  def do_OPTIONS(self):
    self.send_response(204)
    self._send_cors_headers()
    self.end_headers()

  def _send_cors_headers(self):
    origin = self.headers.get("Origin")
    if origin:
      self.send_header("Access-Control-Allow-Origin", origin)
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

  def _json_response(self, object: R):
    payload = json.dumps(object).encode("utf-8")

    self.send_response(200)
    self.send_header("Content-Type", "application/json")
    self.send_header("Content-Length", str(len(payload)))
    self.end_headers()
    self.wfile.write(payload)

  def _handle_post(self, fn: Callable[[P], R]):
    try:
      content_length = int(self.headers.get("Content-Length", 0))
      body = self.rfile.read(content_length).decode("utf-8")
      payload_in = json.loads(body)
      result: R = fn(payload_in)

      self._json_response(result)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def _post_query_images(self):
    class Payload(TypedDict):
      wkt: str

    def logic(payload: Payload) -> list[dict[str, Any]]:
      wkt = payload["wkt"]
      return get_images_by_intersection(wkt)

    self._handle_post(logic)

  def _post_image_info(self):
    class Payload(TypedDict):
      id: str

    def logic(payload: Payload):
      hash = decode_sha256_from_b64(payload["id"])
      return get_image_info(hash)

    self._handle_post(logic)

  def _post_parametric_params(self):
    class Payload(TypedDict):
      id: str

    def logic(payload: Payload):
      hash = decode_sha256_from_b64(payload["id"])
      return get_radiometric_parameters(hash, ("noise", "sigma0"))

    self._handle_post(logic)

  def _post_search_equipment(self):
    class Payload(TypedDict):
      query: str

    def logic(payload: Payload):
      query = payload["query"]
      return search_equipment(query)

    self._handle_post(logic)

  def _post_update_attributes(self, table: str):
    def logic(payload: AttributeUpdate):
      update_attributes(table, payload)
      return {"message": "Successfully updated attributes"}

    if not table or table not in ATTRIBUTE_TABLES:
      self.send_error(404, "Invalid POST endpoint")
      return

    self._handle_post(logic)

  def _post_update_annotation(self):
    def logic(payload: AnnotationUpdate):
      update_annotation(payload)
      return {"message": "Successfully updated annotations"}

    self._handle_post(logic)

  def _get_attribute_tables(self):
    try:
      tables = get_attribute_tables()
      result = {"tables": tables}
      self._json_response(result)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def _get_attribute_schema(self, table: str):
    if not table or table not in ATTRIBUTE_TABLES:
      self.send_error(404, "Invalid POST endpoint")
      return

    try:
      attribute_schema = get_attribute_schema(table)
      self._json_response(attribute_schema)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def _get_attributes(self, table: str):
    if not table or table not in ATTRIBUTE_TABLES:
      self.send_error(404, "Invalid POST endpoint")
      return

    try:
      attribute_options = get_attribute_data(table, True)
      result = {"options": attribute_options}
      self._json_response(result)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def _get_attribute_data(self, table: str):
    if not table or table not in ATTRIBUTE_TABLES:
      self.send_error(404, "Invalid POST endpoint")
      return

    try:
      attribute_data = get_attribute_data(table)
      result = {"data": attribute_data}
      self._json_response(result)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def _get_annotations(self, image_id: str):
    image_hash = decode_sha256_from_b64(image_id)
    annotations = get_annotations(image_hash)
    self._json_response(annotations)
