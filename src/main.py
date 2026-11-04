import sys
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from pydantic_ai.models.function import FunctionModel

from config import settings
from dag.agents.agents import (
    build_agent_activities,
    build_agent_destination,
    build_agent_flight,
    build_agent_hotel,
)
from dag.agents.mocks import mock_activities, mock_destination, mock_flight, mock_hotel
from dag.utils.api_client import APIClient
from dag.workflows.router import Router, RouterDeps
from dag.workflows.travel_planner import API, Agents, TravelDeps, TravelPlanner
from database import QdrantDatabase

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


planner = TravelPlanner(
    deps=TravelDeps(
        retries=2,
        wheather=cast("API", APIClient("https://api.open-meteo.com")),
    ),
    agents=Agents(
        destination=build_agent_destination(
            file_path=Path("src/dag/config/destination.yaml"),
            mock_model=FunctionModel(mock_destination),
        ),
        flight=build_agent_flight(
            file_path=Path("src/dag/config/flight.yaml"),
            mock_model=FunctionModel(mock_flight),
        ),
        hotel=build_agent_hotel(
            file_path=Path("src/dag/config/hotel.yaml"),
            mock_model=FunctionModel(mock_hotel),
        ),
        activity=build_agent_activities(
            file_path=Path("src/dag/config/activities.yaml"),
            mock_model=FunctionModel(mock_activities),
        ),
    ),
).build()

router = Router(
    deps=RouterDeps(
        graph=planner,
        database=QdrantDatabase(
            url=settings.qdrant_host,
            collection_name=settings.collection_name,
        ),
    )
).build()


def get_graph():
    """FastAPI dependency: inject the compiled LangGraph into the routes."""
    return planner


def get_router():
    """FastAPI dependency: inject the compiled LangGraph into the routes."""
    return router


def main() -> None:
    # repo root on sys.path so `src.routes` resolves when run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import uvicorn

    uvicorn.run("routes:app", host="127.0.0.1", port=settings.port)


if __name__ == "__main__":
    main()
