import uuid
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request

from dag.errors import ForbiddenError
from dag.services.travel_planner import Triage, TripState, ValidationResult
from logger import request_id
from main import graph

router = APIRouter()
app = FastAPI()
app.include_router(router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    # trust the client's header if given, else mint one; echo it back
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = request_id.set(rid)
    try:
        response = await call_next(request)
    finally:
        request_id.reset(token)
    response.headers["x-request-id"] = rid
    return response


@router.get("/query")
async def query_rag_system(query: str) -> dict[str, Any]:
    try:
        response = await graph.ainvoke(
            TripState(
                user_id=uuid.uuid7(),
                user_input="Plan a trip to Tokyo with a hotel and activities",
                origin_city="Barcelona",
                triage=Triage(
                    category="general", priority="normal", reason="initial request"
                ),
                validation=ValidationResult(passed=False),
                retry_count=0,
            )
        )
        return {"query": query, "response": response}
    except ForbiddenError:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

