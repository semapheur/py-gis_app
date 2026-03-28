from http.server import ThreadingHTTPServer

from src.bootstrap import get_settings
from src.server import Handler

if __name__ == "__main__":
  settings = get_settings()

  print(f"Serving {settings.HOST}:{settings.PORT}")
  server = ThreadingHTTPServer((settings.HOST, settings.PORT), Handler)
  server.serve_forever()
