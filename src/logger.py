import atexit
import datetime as dt
import json
import logging
import sqlite3
import sys
import uuid
from queue import Queue
from typing import override

from src.bootstrap import get_settings
from src.sqlite.table import Field, Table, datetime_field, uuid_field
from src.timeutils import datetime_to_unix

app_settings = get_settings()

LOG_RECORD_BUILTIN_ATTRS = {
  "args",
  "asctime",
  "created",
  "exc_info",
  "exc_text",
  "filename",
  "funcName",
  "levelname",
  "levelno",
  "lineno",
  "module",
  "msecs",
  "message",
  "msg",
  "name",
  "pathname",
  "process",
  "processName",
  "relativeCreated",
  "stack_info",
  "thread",
  "threadName",
  "taskName",
}


class LoggerTable(Table):
  _table_name = "logs"
  id = uuid_field(True, False)
  datetime = datetime_field(False)
  level = Field(str, nullable=False)
  logger = Field(str, nullable=False)
  record = Field(str, nullable=False)


class JsonFormatter(logging.Formatter):
  def __init__(
    self,
    *,
    fmt_keys: dict[str, str] | None = None,
  ):
    super().__init__()
    self.fmt_keys = fmt_keys if fmt_keys is not None else {}

  @override
  def format(self, record: logging.LogRecord) -> str:
    message = self._prepare_log_dict(record)
    return json.dumps(message, default=str)

  def _prepare_log_dict(self, record: logging.LogRecord):
    always_fields = {
      "message": record.getMessage(),
      "timestamp": datetime_to_unix(
        dt.datetime.fromtimestamp(record.created, tz=dt.timezone.utc)
      ),
    }
    if record.exc_info is not None:
      always_fields["exc_info"] = self.formatException(record.exc_info)

    if record.stack_info is not None:
      always_fields["stack_info"] = self.formatStack(record.stack_info)

    message = {
      key: msg_val
      if (msg_val := always_fields.pop(val, None)) is not None
      else getattr(record, val)
      for key, val in self.fmt_keys.items()
    }
    message.update(always_fields)

    for key, val in record.__dict__.items():
      if key not in LOG_RECORD_BUILTIN_ATTRS:
        message[key] = val

    return message


class SqliteHandler(logging.Handler):
  def __init__(self):
    super().__init__()
    self.conn = sqlite3.connect(app_settings.LOG_DB, check_same_thread=False)

  def _create_table(self):
    table_sql = LoggerTable.create_table_sql()
    self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_sql}")

  def emit(self, record: logging.LogRecord):
    try:
      message = json.loads(self.format(record))

      self.conn.execute(
        "INSERT INTO logs (id, timestamp, level, logger, record) VALUES (?, ?, ?, ?, ?)",
        (
          uuid.uuid4(),
          message.pop("timestamp"),
          message.pop("level"),
          message.pop("logger"),
          json.dumps(message),
        ),
      )
      self.conn.commit()
    except Exception:
      self.handleError(record)

  def close(self):
    self.conn.close()
    super().close()


def setup_logging():
  log_queue = Queue()

  stderr_handler = logging.StreamHandler(sys.stderr)
  stderr_handler.setFormatter(
    logging.Formatter(
      "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
      datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
  )

  sqlite_handler = SqliteHandler()
  sqlite_handler.setFormatter(
    JsonFormatter(
      fmt_keys={
        "level": "levelname",
        "logger": "name",
        "lineno": "lineno",
        "func": "funcName",
        "module": "module",
        "thread": "threadName",
        "process": "processName",
      }
    )
  )

  listener = logging.handlers.QueueListener(
    log_queue, stderr_handler, sqlite_handler, respect_handler_level=True
  )

  queue_handler = logging.handlers.QueueHandler(log_queue)
  root = logging.getLogger()
  root.setLevel(logging.DEBUG)
  root.addHandler(queue_handler)

  listener.start()
  atexit.register(listener.stop)

  return listener
