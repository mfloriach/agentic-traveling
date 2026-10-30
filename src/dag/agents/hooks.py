from pydantic_ai import ModelRequestContext, RunContext
from pydantic_ai.capabilities import Hooks

from logger import logger

acl = Hooks()


@acl.on.before_model_request
async def log_request(
    ctx: RunContext, request_context: ModelRequestContext
) -> ModelRequestContext:
    logger.info(f"Sending {len(request_context.messages)} messages to the model")
    # > Sending 1 messages to the model
    return request_context
