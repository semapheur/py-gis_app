import json
import logging
import mimetypes
import os
import re
from http.server import SimpleHTTPRequestHandler
from io import BufferedReader
from typing import Any, Callable, TypeVar

from src.bootstrap import get_settings
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
      index = full_path / "index.html"
      if index.exists():
        return str(index)
      return str(app_settings.STATIC_DIR / "200.html")

    if full_path.exists():
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
