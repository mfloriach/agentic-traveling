from pathlib import Path

from pydantic_ai.models.function import FunctionModel

from src.retriever.agents.agents import (
    build_agent_activities,
    build_agent_destination,
    build_agent_flight,
    build_agent_hotel,
)
from src.retriever.agents.mocks import (
    mock_activities,
    mock_destination,
    mock_flight,
    mock_hotel,
)
from src.retriever.utils.api_client import APIClient

from .travel_planner import Agents, TravelDeps, TravelPlanner

planner = TravelPlanner(
    deps=TravelDeps(
        retries=2,
        wheather=APIClient("https://api.open-meteo.com"),
    ),
    agents=Agents(
        destination=build_agent_destination(
            file_path=Path("src/retriever/config/destination.yaml"),
            mock_model=FunctionModel(mock_destination),
        ),
        flight=build_agent_flight(
            file_path=Path("src/retriever/config/flight.yaml"),
            mock_model=FunctionModel(mock_flight),
        ),
        hotel=build_agent_hotel(
            file_path=Path("src/retriever/config/hotel.yaml"),
            mock_model=FunctionModel(mock_hotel),
        ),
        activity=build_agent_activities(
            file_path=Path("src/retriever/config/activities.yaml"),
            mock_model=FunctionModel(mock_activities),
        ),
    ),
)
