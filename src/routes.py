import uuid
from typing import Annotated, Any

import logfire
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from dag.errors import ForbiddenError
from dag.workflows.travel_planner import Triage, TripState, ValidationResult
from logger import logger, request_id, user_id
from main import get_graph

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
    graph: Annotated[Any, Depends(get_graph)],
) -> dict[str, Any]:
    uid = uuid.uuid7()
    token = user_id.set(str(uid))
    try:
        with logfire.span(
            "travel.request",
            request_id=request_id.get(),
            user_id=user_id.get(),
        ):
            response = await graph.ainvoke(
                TripState(
                    user_id=uid,
                    user_input=query.query,
                    origin_city="Barcelona",
                    triage=Triage(
                        category="general", priority="normal", reason="initial request"
                    ),
                    validation=ValidationResult(passed=False),
                    retry_count=0,
                ),
                config=RunnableConfig(
                    # happy path = 6 super-steps; +5 per retry round-trip.
                    # 25 (langgraph default) covers retries=2 with slack.
                    # recursion_limit=3,
                    max_concurrency=10,
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
