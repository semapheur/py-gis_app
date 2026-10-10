import contextlib
import copy
import datetime as dt
import json
import logging
import logging.handlers
import sqlite3
import sys
import threading
import uuid
from contextvars import ContextVar
from queue import SimpleQueue
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

DEFAULT_FMT_KEYS = {
  "lineno": "lineno",
  "func": "funcName",
  "module": "module",
  "thread": "threadName",
  "process": "processName",
}


def _timestamp(record: logging.LogRecord):
  return datetime_to_unix(dt.datetime.fromtimestamp(record.created, tz=dt.UTC))


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
    self.fmt_keys = DEFAULT_FMT_KEYS if fmt_keys is None else fmt_keys

  @override
  def format(self, record: logging.LogRecord) -> str:
    return json.dumps(self.to_dict(record), default=str)

  def to_dict(self, record: logging.LogRecord):
    always_fields = {
      "message": record.getMessage(),
      "timestamp": _timestamp(record),
    }
    if record.exc_info and record.exc_info[0] is not None:
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


class StructuredQueueHandler(logging.handlers.QueueHandler):
  @override
  def prepare(self, record: logging.LogRecord) -> logging.LogRecord:
    record = copy.copy(record)
    record.msg = record.getMessage()  # resolve %-args now; args may not be safe later
    record.args = None
    return record


class SqliteHandler(logging.Handler):
  def __init__(self, formatter: JsonFormatter | None = None):
    super().__init__()
    self.setFormatter(formatter or JsonFormatter())
    self._conn: sqlite3.Connection | None = None
    self._conn_lock = threading.Lock()

  def _connection(self) -> sqlite3.Connection:
    if self._conn is None:
      conn = sqlite3.connect(app_settings.LOG_DB, timeout=100, check_same_thread=False)
      conn.execute("PRAGMA journal_mode=WAL")
      conn.execute("PRAGMA synchronous=NORMAL")
      conn.execute("PRAGMA busy_timeout=10000")
      conn.execute(LoggerTable.create_table_sql())
      conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_datetime ON logs(datetime)")
      conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level, datetime)")
      conn.commit()
      self._conn = conn

    return self._conn

  @override
  def emit(self, record: logging.LogRecord):
    try:
      formatter = self.formatter
      assert isinstance(formatter, JsonFormatter)
      data = formatter.to_dict(record)
      for key in ("timestamp", "level", "logger"):
        data.pop(key, None)

      with self._conn_lock:
        conn = self._connection()
        conn.execute(
          "INSERT INTO logs (id, datetime, level, logger, record) VALUES (?, ?, ?, ?, ?)",
          (
            uuid.uuid4().bytes,
            _timestamp(record),
            record.levelname,
            record.name,
            json.dumps(data, default=str),
          ),
        )
        conn.commit()
    except Exception:
      self.handleError(record)

  def prune(self, older_than_days: int) -> int:
    cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(days=older_than_days)
    with self._conn_lock:
      conn = self._connection()
      cur = conn.execute("DELETE FROM logs WHERE datetime < ?", (cutoff,))
      conn.commit()
      return cur.rowcount

  @override
  def close(self):
    with self._conn_lock:
      if self._conn is not None:
        self._conn.close()
        self._conn = None

    super().close()


request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestContextFilter(logging.Filter):
  def filter(self, record: logging.LogRecord):
    rid = request_id_var.get()
    if rid is not None:
      record.request_id = rid

    return True


@contextlib.contextmanager
def logging_context(*, level: int = logging.INFO, retention_days: int | None = 30):
  stderr_handler = logging.StreamHandler(sys.stderr)
  stderr_handler.setLevel(level)
  stderr_handler.setFormatter(
    logging.Formatter(
      "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
      datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
  )

  sqlite_handler = SqliteHandler(JsonFormatter())
  sqlite_handler.setLevel(level)

  if retention_days is not None:
    try:
      sqlite_handler.prune(retention_days)
    except sqlite3.Error:
      logging.getLogger(__name__).exception("Failed to prune log database")

  log_queue = SimpleQueue()
  queue_handler = StructuredQueueHandler(log_queue)
  queue_handler.addFilter(RequestContextFilter())

  root = logging.getLogger()
  previous_level = root.level
  root.addHandler(queue_handler)
  root.setLevel(level)

  try:
    with logging.handlers.QueueListener(
      log_queue, stderr_handler, sqlite_handler, respect_handler_level=True
    ):
      yield
  finally:
    root.removeHandler(queue_handler)
    root.setLevel(previous_level)
    sqlite_handler.close()
