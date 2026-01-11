import os
from http.server import ThreadingHTTPServer

from src.server import Handler

if __name__ == "__main__":
  host = os.getenv("HOST", "0.0.0.0")
  port = int(os.getenv("PORT", "8080"))

  print(f"Serving {host}:{port}")
  server = ThreadingHTTPServer((host, port), Handler)
  server.serve_forever()
