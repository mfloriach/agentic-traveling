from pathlib import Path

from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic_ai.models.function import FunctionModel

from src.config import settings
from src.dag.agents.agents import (
    build_agent_activities,
    build_agent_destination,
    build_agent_flight,
    build_agent_hotel,
)
from src.dag.agents.mocks import (
    mock_activities,
    mock_destination,
    mock_flight,
    mock_hotel,
)
from src.dag.utils.api_client import APIClient
from src.dag.workflows.router import Router, RouterDeps
from src.dag.workflows.travel_planner import Agents, TravelDeps, TravelPlanner
from src.database import QdrantDatabase
from src.redis import SemanticCacheValkey

load_dotenv(Path(__file__).resolve().parents[1] / ".env")


planner = TravelPlanner(
    deps=TravelDeps(
        retries=2,
        wheather=APIClient("https://api.open-meteo.com"),
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

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

router = Router(
    deps=RouterDeps(
        graph=planner,
        database=QdrantDatabase(
            url=settings.qdrant_host,
            collection_name=settings.collection_name,
            embeddings=embeddings,
        ),
        cache=SemanticCacheValkey(embeddings=embeddings),
    )
).build()


def get_graph():
    """FastAPI dependency: inject the compiled LangGraph into the routes."""
    return planner


def get_router():
    """FastAPI dependency: inject the compiled LangGraph into the routes."""
    return router
