import logging
import logfire

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logfire.configure(send_to_logfire="if-token-present")
logfire.instrument_pydantic_ai()


logger = logging.getLogger("travel_planner")