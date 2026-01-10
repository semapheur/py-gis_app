import json
import mimetypes
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BufferedReader
from typing import Any, Callable, TypedDict, TypeVar

from src.const import ATTRIBUTE_DB, STATIC_DIR
from src.hashing import decode_sha256_from_b64
from src.index.images import get_image_info, get_images_by_intersection
from src.index.radiometric import get_radiometric_parameters
from src.spatialite import get_tables

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
      self.handle_attribute_tables()
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
    if self.path == "/api/query-images":
      self.handle_query_images()
      return

    if self.path == "/api/image-info":
      self.handle_image_info()
      return

    if self.path == "/api/radiometric-params":
      self.handle_parametric_params()
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

  def _json_response(self, payload: bytes):
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
      payload_out = json.dumps(result).encode("utf-8")

      self._json_response(payload_out)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")

  def handle_query_images(self):
    class Payload(TypedDict):
      wkt: str

    def logic(payload: Payload) -> list[dict[str, Any]]:
      wkt = payload["wkt"]
      return get_images_by_intersection(wkt)

    self._handle_post(logic)

  def handle_image_info(self):
    class Payload(TypedDict):
      id: str

    def logic(payload: Payload):
      hash = decode_sha256_from_b64(payload["id"])
      return get_image_info(hash)

    self._handle_post(logic)

  def handle_parametric_params(self):
    class Payload(TypedDict):
      id: str

    def logic(payload: Payload):
      hash = decode_sha256_from_b64(payload["id"])
      return get_radiometric_parameters(hash, ("noise", "sigma0"))

    self._handle_post(logic)

  def handle_attribute_tables(self):
    try:
      tables = get_tables(ATTRIBUTE_DB)

      payload = json.dumps({"tables": tables}).encode("utf-8")
      self._json_response(payload)

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")


if __name__ == "__main__":
  host = os.getenv("HOST", "0.0.0.0")
  port = int(os.getenv("PORT", "8080"))

  print(f"Serving {host}:{port}")
  server = ThreadingHTTPServer((host, port), Handler)
  server.serve_forever()
