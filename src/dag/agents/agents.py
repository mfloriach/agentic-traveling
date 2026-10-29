from pydantic_ai import Agent

# from pydantic_ai.exceptions import (
#     ModelRateLimitError,
#     ModelServerError,
#     ModelUnavailableError,
# )
# from pydantic_ai.models.fallback import FallbackModel
from ..services.travel_planner import TravelDeps
from .schemas import Activities, DestinationOutput, FlightPlan, HotelOption
from .tools import get_weather

# with open("agents.yml") as f:
#     configs = yaml.safe_load(f)


destination = Agent.from_file(
    "./config/destination.yaml",
    # model=FallbackModel(
    #     configs["destination"]["model"],
    #     *configs["destination"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    deps_type=TravelDeps,
    output_type=DestinationOutput,
    tools=[get_weather],
)


flight = Agent.from_file(
    "./config/flight.yaml",
    # model=FallbackModel(
    #     configs["flight"]["model"],
    #     *configs["flight"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    deps_type=TravelDeps,
    output_type=FlightPlan,
)


hotel = Agent.from_file(
    "./config/hotel.yaml",
    # model=FallbackModel(
    #     configs["hotel"]["model"],
    #     *configs["hotel"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    deps_type=TravelDeps,
    output_type=HotelOption,
)


activities = Agent.from_file(
    "./config/activities.yaml",
    # model=FallbackModel(
    #     configs["activities"]["model"],
    #     *configs["activities"]["fallback_models"],
    #     fallback_on=(
    #         ModelRateLimitError,
    #         ModelUnavailableError,
    #         ModelServerError,
    #     ),
    # ),
    deps_type=TravelDeps,
    output_type=Activities,
)
