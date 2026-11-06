import uuid
from pathlib import Path
from typing import Annotated, Any

import opentelemetry.trace as trace
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from src.logger import logger, request_id, user_id
from src.retriever.errors import ForbiddenError
from src.retriever.workflows.router.graph import QueryState
from src.retriever.workflows.router.graph import app as router

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI()


def get_router():
    """FastAPI dependency: inject the compiled LangGraph into the routes."""
    return router


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


@app.get("/query")
async def query_rag_system(
    query: Annotated[Search, Query()],
    router: Annotated[Any, Depends(get_router)],
) -> dict[str, Any]:
    uid = uuid.uuid7()
    token = user_id.set(str(uid))
    try:
        with trace.get_tracer("rag").start_as_current_span(
            "travel.request",
            attributes={
                "request_id": request_id.get(),
                "user_id": user_id.get(),
                # TODO: investigate how to get session id from request context
                "session_id": user_id.get(),
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
                    # TODO: investigate if this is needed for our use case
                    # recursion_limit=3,
                    # TODO: investigate if this is needed for our use case
                    max_concurrency=10,
                ),
            )
            return {"query": query.query, "response": response}
    except ForbiddenError as e:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        ) from e
    except Exception as e:
        logger.exception("Request failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        user_id.reset(token)
