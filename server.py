import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from src.env import load_env
from src.geometry import Polygon
from src.imagery_index import select_images_by_intersection

load_env()

STATIC_DIR = os.getenv("STATIC_DIR", "./static")
INDEX_DB = Path(os.getenv("DB_DIR", "db")) / "index.db"


class Handler(SimpleHTTPRequestHandler):
  def translate_path(self, path: str) -> str:
    if path.startswith("/api"):
      return path

    rel = path.lstrip("/")
    full = os.path.join(STATIC_DIR, rel)
    print(full)

    if os.path.isdir(full):
      return os.path.join(STATIC_DIR, "index.html")

    if os.path.exists(full):
      return full

    return super().translate_path(path)

  def do_POST(self):
    if self.path == "/api/query-images":
      self.handle_query_images()
      return

    self.send_error(404, "Unknown POST endpoint")

  def handle_query_images(self):
    try:
      content_length = int(self.headers.get("Content-Length", 0))
      body = self.rfile.read(content_length).decode("utf-8")
      polygon_geojson = json.loads(body)

      polygon = Polygon.parse_geojson(polygon_geojson)
      result = select_images_by_intersection(INDEX_DB, polygon)

      self.send_response(200)
      self.send_header("Content-Type", "application/json")
      self.end_headers()
      self.wfile.write(json.dumps(result).encode("utf-8"))

    except Exception as e:
      self.send_error(500, f"Server error: {str(e)}")


if __name__ == "__main__":
  host = os.getenv("HOST", "0.0.0.0")
  port = int(os.getenv("PORT", "8080"))

  print(f"Serving {host}:{port}")
  server = HTTPServer((host, port), Handler)
  server.serve_forever()
