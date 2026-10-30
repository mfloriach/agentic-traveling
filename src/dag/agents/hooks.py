from pydantic_ai import RunContext
from pydantic_ai.capabilities import Hooks

from logger import logger

acl = Hooks()


@acl.on.before_run
async def log_request(ctx: RunContext) -> None:
    logger.info(
        "Agent run started: asdsadas",
    )
