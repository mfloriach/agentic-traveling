import uuid
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException

from dag.errors import ForbiddenError
from dag.services.travel_planner import Triage, TripState, ValidationResult
from main import graph

router = APIRouter()


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


app = FastAPI()
app.include_router(router)
