import contextvars
import logging

import logfire

# correlation id for the current request; "-" outside requests
request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)


class RequestIdFilter(logging.Filter):
    """Attach the current request_id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(request_id)s] %(name)s %(message)s",
)
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()


logger = logging.getLogger("travel_planner")
