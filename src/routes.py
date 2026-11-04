import uuid
from typing import Annotated, Any

import opentelemetry.trace as trace
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from dag.errors import ForbiddenError
from logger import logger, request_id, user_id
from main import get_router, router
from src.dag.workflows.router import QueryState

router = APIRouter()
app = FastAPI()
app.include_router(router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id.reset(token)
    response.headers["x-request-id"] = rid
    return response


class Search(BaseModel):
    query: str = Field(min_length=3, max_length=3000)


@router.get("/query")
async def query_rag_system(
    query: Annotated[Search, Query()],
    router: Annotated[Any, Depends(get_router)],
) -> dict[str, Any]:
    uid = uuid.uuid7()
    token = user_id.set(str(uid))
    try:
        with trace.get_tracer(
            "rag"
        ).start_as_current_span(
            "travel.request",
            attributes={
                "request_id": request_id.get(),
                "user_id": user_id.get(),
                "session_id": user_id.get(),  # TODO: investigate how to get session id from request context
            },
        ):
            response = await router.ainvoke(
                QueryState(
                    user_id=uid,
                    query=query.query,
                ),
                config=RunnableConfig(
                    # happy path = 6 super-steps; +5 per retry round-trip.
                    # 25 (langgraph default) covers retries=2 with slack.
                    # recursion_limit=3, #TODO: investigate if this is needed for our use case
                    max_concurrency=10,  # TODO: investigate if this is needed for our use case
                ),
            )
            return {"query": query.query, "response": response}
    except ForbiddenError:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )
    except Exception as e:
        logger.exception("Request failed")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        user_id.reset(token)
