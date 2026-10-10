import logging
import signal
import webbrowser
from http.server import ThreadingHTTPServer

from src.bootstrap import get_settings
from src.logger import logging_context
from src.seed import create_db_tables
from src.server.api_routes import ApiRoutes

logger = logging.getLogger(__name__)


class LoggingHTTPServer(ThreadingHTTPServer):
  def handle_error(self, request, client_address):
    logger.exception(
      "Unhandled error while handling requests from %s", client_address[0]
    )


def _raise_system_exit(signum, frame):
  raise SystemExit()


if __name__ == "__main__":
  settings = get_settings()

  with logging_context():
    signal.signal(signal.SIGTERM, _raise_system_exit)
  try:
    create_db_tables()

    print(f"Serving {settings.HOST}:{settings.PORT}")

    if settings.APP_MODE == "production":
      webbrowser.open(f"http://localhost:{settings.PORT}")

    server = LoggingHTTPServer((settings.HOST, settings.PORT), ApiRoutes)
    try:
      server.serve_forever()
    finally:
      server.server_close()

  except KeyboardInterrupt, SystemExit:
    logger.info("Shutting down")
  except Exception:
    logger.exception("Fatal error, server stopped")
    raise
