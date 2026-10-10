import json
import logging
import mimetypes
import os
import re
import time
import uuid
from http.server import SimpleHTTPRequestHandler
from io import BufferedReader
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

from src.bootstrap import get_settings
from src.logger import request_id_var
from src.msgpack import decode_msgpack, encode_msgpack

MAX_BODY = 50 * 1024 * 1024

app_settings = get_settings()

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("http.access")


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
    url_path = unquote(urlsplit(path).path)
    if url_path.startswith("/api/"):
      return url_path

    root = app_settings.STATIC_DIR.resolve()
    try:
      full_path = (root / url_path.lstrip("/")).resolve()
    except ValueError, OSError:
      return str(root / "200.html")

    if not full_path.is_relative_to(root):
      return str(root / "200.html")

    if full_path.is_dir():
      index = full_path / "index.html"
      return str(index if index.exists() else root / "200.html")

    return str(full_path)

  def handle_one_request(self):
    self.command = None
    self.path = ""
    self._status: int | str = "-"
    self._t0 = time.perf_counter()
    request_id_var.set(uuid.uuid4().hex[:8])
    try:
      return super().handle_one_request()
    finally:
      if self.command:
        self._log_access()

  def _log_access(self):
    ms = (time.perf_counter() - self._t0) * 1000
    status = self._status if isinstance(self._status, int) else 0
    if status >= 500:
      level = logging.ERROR
    elif status >= 400:
      level = logging.WARNING
    elif self.path.startswith("/api/"):
      level = logging.INFO
    else:
      level = logging.DEBUG

    access_logger.log(
      level,
      "%s %s -> %s (%.0f ms)",
      self.command,
      self.path,
      self._status,
      ms,
      extra={
        "client": self.client_address[0],
        "status": self._status,
        "method": self.command,
        "duration_ms": round(ms, 1),
      },
    )

  def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
    self._status = (
      code if isinstance(code, int) else int(code) if str(code).isdigit() else code
    )

  def log_error(self, format: str, *args: Any) -> None:
    access_logger.debug(format, *args)

  def log_message(self, format: str, *args: Any) -> None:
    access_logger.info(format, *args)

  def _serve_static(self):
    path = self.translate_path(self.path)
    if not os.path.exists(path):
      self.send_error(404, "File not found")
      return

    file_size = os.path.getsize(path)
    content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"

    range_header = self.headers.get("Range")

    if range_header:
      try:
        _, rng = range_header.strip().split("=", 1)
        start_str, end_str = rng.split(",")[0].split("-", 1)
        if start_str == "":
          start = max(file_size - int(end_str), 0)
          end = file_size - 1
        else:
          start = int(start_str)
          end = int(end_str) if end_str else file_size - 1
          end = min(end, file_size - 1)

        if start > end or start >= file_size:
          raise ValueError
      except ValueError:
        self.send_response(416)
        self._send_cors_headers()
        self.send_header("Content-Range", f"bytes */{file_size}")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return

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
      except ConnectionError:
        break
      remaining -= len(chunk)

  def _read_body(self) -> bytes:
    length = int(self.headers.get("Content-Length", 0))
    if not 0 <= length <= MAX_BODY:
      raise ValueError(f"Invalid Content-Length: {length}")
    return self.rfile.read(length)

  def _read_payload(self):
    try:
      return decode_msgpack(self._read_body())
    except Exception as e:
      logger.warning("Bad request body for %s: %s", self.path, e)
      raise ApiError(400, "Bad request") from e

  def _respond(self, call: Callable[[], Any]):
    try:
      status = 200
      payload = encode_msgpack(call())
    except ApiError as e:
      status = e.status
      payload = encode_msgpack({"detail": e.message})
    except Exception:
      logger.exception("Error handling %s", self.path)
      status = 500
      payload = encode_msgpack(
        {"detail": f"Server error (requst {request_id_var.get()})"}
      )

    self._send_msgpack(status, payload)

  def _send_msgpack(self, status: int, payload: bytes):
    try:
      self.send_response(status)
      self.send_header("Content-Type", "application/msgpack")
      self.send_header("Content-Length", str(len(payload)))
      self.end_headers()
      self.wfile.write(payload)
    except ConnectionError:
      logger.debug("Client disconnected before response to %s was sent", self.path)

  def _error_response(self, status: int, message: str):
    self._send_msgpack(status, encode_msgpack({"detail": message}))

  def _invoke(self, fn: Callable, stream: bool, path_params: dict[str, str]):
    if stream:
      self._invoke_stream(fn, path_params)
    elif self.command == "POST":
      self._invoke_post(fn, path_params)
    else:
      self._invoke_get(fn, path_params)

  def _invoke_get(self, fn: Callable, path_params: dict[str, str]):
    self._respond(lambda: fn(self, **path_params))

  def _invoke_post(self, fn: Callable, path_params: dict[str, str]):
    self._respond(lambda: fn(self, self._read_payload(), **path_params))

  def _invoke_stream(self, fn: Callable, path_params: dict[str, str]):
    try:
      payload = self._read_payload()
    except ApiError as e:
      self._error_response(e.status, e.message)
      return

    self.send_response(200)
    self.send_header("Content-Type", "text/event-stream")
    self.send_header("Cache-Control", "no-cache")
    self.send_header("X-Accel-Buffering", "no")
    self.end_headers()

    client_gone = False

    def send_event(event: str, data: dict):
      nonlocal client_gone
      if client_gone:
        return
      try:
        chunk = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        self.wfile.write(chunk.encode("utf-8"))
        self.wfile.flush()
      except ConnectionError, TimeoutError:
        client_gone = True
        logger.info(
          "Client disconnected from stream %s; continuing in background", self.path
        )

    try:
      fn(self, payload, send_event, **path_params)
      send_event("done", {"message": "OK"})
    except Exception:
      logger.exception("Error in stream handler")
      send_event("error", {"message": f"Server error (request {request_id_var.get()})"})

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
        params = {k: unquote(v) for k, v in m.groupdict().items()}
        self._invoke(fn, stream, params)
        return True

    return False

  def _api_response(self, obj: Any):
    payload = encode_msgpack(obj)
    self.send_response(200)
    self.send_header("Content-Type", "application/msgpack")
    self.send_header("Content-Length", str(len(payload)))
    self.end_headers()
    self.wfile.write(payload)

  def do_GET(self):
    if self._dispatch("GET"):
      return

    if self.path.startswith("/api/"):
      self._error_response(404, "Unknown GET endpoint")
      return

    self._serve_static()

  def do_POST(self):
    if self._dispatch("POST"):
      return

    self._error_response(404, "Unknown POST endpoint")

  def do_OPTIONS(self):
    self.send_response(204)
    self._send_cors_headers()
    self.end_headers()
