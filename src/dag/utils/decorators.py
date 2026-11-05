import logging
import time
from functools import wraps

logger = logging.getLogger("travel_planner")


def log_agent(func):
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        agent_name = func.__name__
        start = time.perf_counter()

        logger.info(
            "agent.started",
            extra={"agent_name": agent_name},
        )

        try:
            result = await func(self, *args, **kwargs)
            usage = result.usage()

            logger.info(
                "agent.completed",
                extra={
                    "agent_name": agent_name,
                    "duration_ms": round((time.perf_counter() - start) * 1000),
                    "requests": usage.requests,
                    "input_tokens": usage.input_tokens,
                    "output_tokens": usage.output_tokens,
                    "total_tokens": usage.total_tokens,
                },
            )

            return result

        except Exception:
            logger.exception(
                "agent.failed",
                extra={
                    "agent_name": agent_name,
                    "duration_ms": round((time.perf_counter() - start) * 1000),
                },
            )
            raise

    return wrapper
