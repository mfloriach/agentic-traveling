from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel

# from pydantic_ai.exceptions import (
#     ModelRateLimitError,
#     ModelServerError,
#     ModelUnavailableError,
# )
# from pydantic_ai.models.fallback import FallbackModel
from ..workflows.travel_planner import TravelDeps
from .hooks import acl
from .mocks import mock_activities, mock_destination, mock_flight, mock_hotel
from .schemas import ActivitiesOutput, DestinationOutput, FlightOutput, HotelOutput
from .tools import get_weather

# agent spec YAMLs live in dag/config/, resolved from this file (not cwd)
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


destination = Agent.from_file(
    str(_CONFIG_DIR / "destination.yaml"),
    # model=FallbackModel(
    #     configs["destination"]["model"],
    #     *configs["destination"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    model=FunctionModel(mock_destination),
    deps_type=TravelDeps,
    output_type=DestinationOutput,
    # capabilities=[acl],
    tools=[get_weather],
)


flight = Agent.from_file(
    str(_CONFIG_DIR / "flight.yaml"),
    # model=FallbackModel(
    #     configs["flight"]["model"],
    #     *configs["flight"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    model=FunctionModel(mock_flight),
    deps_type=TravelDeps,
    output_type=FlightOutput,
    capabilities=[acl],
)


hotel = Agent.from_file(
    str(_CONFIG_DIR / "hotel.yaml"),
    # model=FallbackModel(
    #     configs["hotel"]["model"],
    #     *configs["hotel"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    model=FunctionModel(mock_hotel),
    deps_type=TravelDeps,
    output_type=HotelOutput,
)


activities = Agent.from_file(
    str(_CONFIG_DIR / "activities.yaml"),
    # model=FallbackModel(
    #     configs["activities"]["model"],
    #     *configs["activities"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    model=FunctionModel(mock_activities),
    deps_type=TravelDeps,
    output_type=ActivitiesOutput,
)
