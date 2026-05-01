from http.server import ThreadingHTTPServer

from src.bootstrap import get_settings
from src.seed import create_db_tables
from src.server import Handler

if __name__ == "__main__":
  settings = get_settings()
  create_db_tables()

  print(f"Serving {settings.HOST}:{settings.PORT}")
  server = ThreadingHTTPServer((settings.HOST, settings.PORT), Handler)
  server.serve_forever()
