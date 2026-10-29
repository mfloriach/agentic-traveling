from typing import Any

from fastapi import APIRouter, HTTPException

from .dag.errors import ForbiddenError
from .dag.services.travel_planner import Services, TravelDeps, TravelPlanner
from .dag.utils.api_client import APIClient

deps = TravelDeps(
    user_name="Alex",
    origin_city="Barcelona",
    services=Services(wheather=APIClient("https://api.open-meteo.com")),
)

planner = TravelPlanner(deps)
app = planner.build()

router = APIRouter()


@router.get("/query")
async def query_rag_system(query: str) -> dict[str, Any]:
    try:
        response = await app.ainvoke(
            {
                "user_input": "Plan a trip to Tokyo with a hotel and activities",
                "retry_count": 0,
            }
        )
        return {"query": query, "response": response}
    except ForbiddenError:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
