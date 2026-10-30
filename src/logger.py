import contextvars
import json
import logging
import sys

# correlation id for the current request; "-" outside requests
request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)
# id of the user this request belongs to; "-" until the request sets it
user_id: contextvars.ContextVar[str] = contextvars.ContextVar("user_id", default="-")


class RequestIdFilter(logging.Filter):
    """Attach the current request_id and user_id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        record.user_id = user_id.get()
        return True


# LogRecord's own attributes; everything else found on the record is caller-supplied
# extra and lands in the JSON payload verbatim
_RECORD_ATTRS = frozenset(
    (
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "request_id",
        "asctime",
    )
)


class JsonFormatter(logging.Formatter):
    """One JSON object per line: standard fields + all caller-provided extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        for key, value in record.__dict__.items():
            if key not in _RECORD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
handler.addFilter(RequestIdFilter())

root = logging.getLogger()
root.addHandler(handler)
root.setLevel(logging.INFO)


logger = logging.getLogger("travel_planner")
